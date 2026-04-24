from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from markupsafe import Markup
from collections import Counter
from flask_bootstrap import Bootstrap

import boto3
import re
import os

if 'AWS_EXECUTION_ENV' in os.environ:
    # Running on AWS Elastic Beanstalk
    application = app = Flask(__name__)
    application.config['SECRET_KEY'] = os.environ.get(
        'FLASK_SECRET_KEY',
        '\xf0?a\x9a\\\xff\xd4;\x0c\xcbHi'
    )
    Bootstrap(application)
    session = boto3.Session()
else:
    # Running locally
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get(
        'FLASK_SECRET_KEY',
        '\xf0?a\x9a\\\xff\xd4;\x0c\xcbHi'
    )
    Bootstrap(app)
    session = boto3.Session(profile_name='swu-admin')

# aws_region = os.environ.get('AWS_REGION')
aws_region = 'us-east-1'
# dynamodb_table = os.environ.get('SWU_DB_TABLE')
dynamodb_table = 'Cards3'
# dynamodb_table = 'Cards-Backup-2'
dynamodb = session.client('dynamodb',
                        region_name=aws_region)


def publish_feedback_to_sns(message):
    """
    Publishes a message to an SNS Topic
    """
    sns = session.client('sns', region_name=aws_region)
    topic_arn = os.environ.get('FEEDBACK_ARN')
    message = f"Message: {message}"

    sns.publish(
        TopicArn=topic_arn,
        Message=message
    )

def get_card(set_id, card_number):
    """
    Given a set id and card number, return the matching card
    """
    response = dynamodb.query(
        TableName=dynamodb_table,
        KeyConditionExpression='setId = :set_id and cardNumber = :card_number',
        ExpressionAttributeValues={
            ':set_id': {'S': set_id},
            ':card_number': {'S': card_number}
        }
    )

    items = response['Items']

    if items:
        # setID and cardNumber are unique so it's safe to just grab the first one
        return process_item(items[0])
    else:
        # Card not found
        return None

def get_price_url(tcg_product_id):
    if not tcg_product_id:
        return None

    response = dynamodb.query(
        TableName='Prices',
        KeyConditionExpression='productId = :pid',
        ExpressionAttributeValues={
            ':pid': {'S': tcg_product_id}
        },
        Limit=1
    )

    items = response.get('Items', [])
    if not items:
        return None

    return items[0].get('url', {}).get('S', None)


def get_variants(base_card_id, current_card_id=None):
    set_info = dynamodb.scan(
        TableName='Sets',
    )
    set_items = set_info.get('Items', [])

    variant_cards = []
    query_kwargs = {
        'TableName': dynamodb_table,
        'IndexName': 'base-card-index',
        'KeyConditionExpression': 'baseCardId = :bid',
        'ExpressionAttributeValues': {
            ':bid': {'S': base_card_id}
        }
    }

    while True:
        response = dynamodb.query(**query_kwargs)
        items = response.get('Items', [])
        for item in items:
            card_id = item.get('cardId', {}).get('S')
            #if current_card_id and card_id == current_card_id:
            #    continue
            variant_card = process_item(item, set_items)
            variant_card['price_url'] = get_price_url(variant_card.get('tcg_product_id'))
            variant_cards.append(variant_card)

        if 'LastEvaluatedKey' not in response:
            break
        query_kwargs['ExclusiveStartKey'] = response['LastEvaluatedKey']

    return variant_cards


def get_next_card(set_id, card_number):

    response = dynamodb.query(
        TableName=dynamodb_table,
        KeyConditionExpression='setId = :set_id and cardNumber > :card_number',
        ExpressionAttributeValues={
            ':set_id': {'S': set_id},
            ':card_number': {'S': card_number}
        },
        Limit=1,
        ScanIndexForward=True
    )

    items = response['Items']

    if items:
        # setID and cardNumber are unique so it's safe to just grab the first one
        return process_item(items[0])
    else:
        # Card not found
        return None


def get_previous_card(set_id, card_number):
    print(card_number)
    response = dynamodb.query(
        TableName=dynamodb_table,
        KeyConditionExpression='setId = :set_id and cardNumber < :card_number',
        ExpressionAttributeValues={
            ':set_id': {'S': set_id},
            ':card_number': {'S': card_number}
        },
        Limit=1,
        ScanIndexForward=False
    )

    items = response['Items']

    if items:
        # setID and cardNumber are unique so it's safe to just grab the first one
        return process_item(items[0])
    else:
        # Card not found
        return None



def search_cards(search_input, sort_field='setnumber', sort_order='asc', leader='', base='', include_variants=False):
    """
    Search the Cards table using the input provided by the user
    Return any matching cards, in the manner specified by sort_field and sort_order
    """
    expressions = []
    current_expression = ""
    quote_stack = []

    variant = ''
    include_all = False

    result_string = ""
    print("sort field ", sort_field)

    for char in search_input:
        if char == " " and not quote_stack:
            if current_expression:
                expressions.append(current_expression)
                current_expression = ""
        elif char == "'":
            if quote_stack and quote_stack[-1] == "'":
                quote_stack.pop()
            else:
                quote_stack.append("'")
        elif char == '"':
            if quote_stack and quote_stack[-1] == '"':
                quote_stack.pop()
            else:
                quote_stack.append('"')
        else:
            current_expression += char

    if current_expression:
        expressions.append(current_expression)

    # Combine adjacent expressions inside quotes into a single expression
    combined_expressions = []
    temp_expression = ""
    for expression in expressions:
        if quote_stack:
            if temp_expression:
                temp_expression += " " + expression
                if quote_stack[-1] == expression[0] and expression[-1] == expression[0]:
                    combined_expressions.append(temp_expression.strip('"').strip("'"))
                    temp_expression = ""
            else:
                temp_expression = expression

        if not quote_stack and temp_expression:
            combined_expressions.append(temp_expression.strip('"').strip("'"))
            temp_expression = ""

    if temp_expression:
        combined_expressions.append(temp_expression.strip('"').strip("'"))

    # Use the combined expressions for further processing
    # print(combined_expressions)

    # Construct the filter expressions for DynamoDB
    filter_expressions = []
    expression_values = {}
    expression_attribute_names = {}
    # print(expressions)
    filter_expression_groups = []
    current_group = []
    counter = 0

    for expression in expressions:
        counter += 1
        filter_expression = ''
        parentheses_removed = 0
        expression = expression.lower()
        if expression == 'or':
            result_string += " or "
            if current_group:
                filter_expression_groups.append(' AND '.join(current_group))
                current_group = []
            continue
        elif expression == 'and':
            result_string += " and "
            continue
        negated = False
        if expression.startswith('-') and len(expression) > 1:
            negated = True
            expression = expression[1:]

        if expression.startswith('('):
            original_length = len(expression)
            expression = expression.lstrip('(')
            stripped_length = len(expression)
            parentheses_removed = original_length - stripped_length
            for x in range(parentheses_removed):
                result_string += " ("
                filter_expression = '('
            parentheses_removed = 0
        elif expression.endswith(')'):
            original_length = len(expression)
            expression = expression.rstrip(')')
            stripped_length = len(expression)
            parentheses_removed = original_length - stripped_length

        if negated:
            result_string += " not"

        if re.search(r'\b(?:a|aspect)(?:<=|<|>|>=|=|:)(.+)', expression):
            attribute_name, comparison_operator, attribute_value = parse_numerical_expression(
                expression)

            if comparison_operator == ':':
                comparison_operator = '>='

            if attribute_value.isdigit():
                result_string += " the aspect count " + comparison_operator + " " + attribute_value
                value_placeholder = f":val_total_{counter}"
                filter_expression += f"#total_count {comparison_operator} {value_placeholder}"
                expression_values[value_placeholder] = {'N': attribute_value}
                expression_attribute_names['#total_count'] = 'totalCount'
            else:
                result_string += " the aspect " + comparison_operator + " " + attribute_value

                if attribute_value in ('vigilance', 'blue'):
                    attribute_value = 'b'
                elif attribute_value in ('command', 'green'):
                    attribute_value = 'g'
                elif attribute_value in ('aggression', 'red'):
                    attribute_value = 'r'
                elif attribute_value in ('cunning', 'yellow'):
                    attribute_value = 'y'
                elif attribute_value in ('heroism', 'white'):
                    attribute_value = 'w'
                elif attribute_value in ('villainy', 'black'):
                    attribute_value = 'k'

                expression_attribute_values = {}

                aspect_counts = {}  # A dictionary to store the counts of each aspect

                # Define the possible aspect abbreviations
                possible_aspects = ['b', 'g', 'r', 'y', 'w', 'k']

                # Initialize counts for all aspects to 0
                for aspect in possible_aspects:
                    aspect_counts[aspect] = 0

                # Count the occurrences of each aspect in the string
                for letter in attribute_value:
                    if letter in possible_aspects:
                        aspect_counts[letter] += 1

                filter_expression_parts = []
                # Loop through the aspect counts dictionary to construct conditions
                for aspect, count in aspect_counts.items():
                    if comparison_operator in ['>', '>='] and count == 0:
                        continue
                    # Use counter-suffixed placeholders so multiple aspect clauses don't collide.
                    expression_attr_name = f'#count_{aspect}_{counter}'
                    expression_attr_value = f':val_{aspect}_{counter}'

                    if comparison_operator == '>':
                        filter_expression_parts.append(f'{expression_attr_name} >= {expression_attr_value}')
                    elif comparison_operator == '<':
                        filter_expression_parts.append(f'{expression_attr_name} <= {expression_attr_value}')
                    else:
                        filter_expression_parts.append(f'{expression_attr_name} {comparison_operator} {expression_attr_value}')

                    # Populate expression attribute names and values
                    expression_attribute_values[expression_attr_value] = {'N': str(count)}
                    expression_attribute_names[expression_attr_name] = f'{aspect}Count'

                if comparison_operator in ('>', '<'):
                    value_placeholder = f":val_total_{counter}"
                    filter_expression_parts.append(f"#total_count {comparison_operator} {value_placeholder}")
                    expression_attribute_values[value_placeholder] = {'N': str(len(attribute_value))}
                    expression_attribute_names['#total_count'] = 'totalCount'

                # Combine all filter conditions with 'AND'
                filter_expression += ' AND '.join(filter_expression_parts)

                expression_values.update(expression_attribute_values)
            
        elif re.match(r'^\w+(?:<=|>=|=|!=|<|>)\d+$', expression):

            # Parse numerical expressions
            attribute_name, comparison_operator, attribute_value = parse_numerical_expression(
                expression)

            if attribute_name == 'p':
                attribute_name = 'power'
                result_string += " the power " 
            elif attribute_name == 'h':
                attribute_name = 'HP'
                result_string += " the hp " 
            elif attribute_name == 'c':
                attribute_name = 'cost'
                result_string += " the cost " 
            elif attribute_name == 'pc':
                attribute_name = 'pilotCost'
                result_string += " the pilot cost " 
            elif attribute_name == 'up':
                attribute_name = 'upgradePower'
                result_string += " the upgrade power " 
            elif attribute_name == 'uh':
                attribute_name = 'upgradeHP'
                result_string += " the upgrade HP " 

            result_string += comparison_operator + " " + attribute_value
            filter_expression += construct_filter_expression(
                attribute_name, comparison_operator)
            expression_values.update(construct_expression_value(
                attribute_name, attribute_value))
            expression_attribute_names.update(
                construct_expression_attribute_name(attribute_name))
        
        else:
            match = re.search(r'\b(?:t|text):(.+)', expression)
            trait = re.search(r'\b(?:tr|trait):(.+)', expression)
            type = re.search(r'\b(?:ty|type):(.+)', expression)
            arena = re.search(r'\b(?:ar|arena):(.+)', expression)
            rarity = re.search(r'\b(?:r|rarity):(.+)', expression)
            event = re.search(r'\b(?:event):(.+)', expression)
            source = re.search(r'\b(?:source):(.+)', expression)
            season = re.search(r'\b(?:season):(.+)', expression)
            card_set = re.search(r'\b(?:s|set):(.+)', expression)
            artist = re.search(r'\b(?:art|artist):(.+)', expression)
            name = re.search(r'(?:name|title):(.+)', expression)
            variant = re.search(r'(?:variant|v):(.+)', expression)
            keyword = re.search(r'\b(?:k|keyword):(.+)', expression)
            rotation = re.search(r'\b(?:rs|rotation):(.+)', expression)
            format_legal = re.search(r'\b(?:f|format):(.+)', expression)
            format_suspended = re.search(r'\b(?:suspended):(.+)', expression)

            if match:
                attribute_name = 'searchText'
                comparison_operator = 'contains'
                attribute_value = match.group(1).lower()
                result_string += " the text includes " + attribute_value

                # Use a unique placeholder for each value
                placeholder_name = f"#{attribute_name}_{counter}"
                value_placeholder = f":{attribute_name}_{counter}"

                # filter_expressions.append(f"contains({placeholder_name}, {value_placeholder})")
                filter_expression += f"contains ({placeholder_name}, {value_placeholder})"
                expression_values.update(construct_expression_value(attribute_name + f"_{counter}", attribute_value, is_numeric=False))
                expression_attribute_names.update({placeholder_name: attribute_name})

                # filter_expression += f"contains (#{attribute_name}, :{attribute_name})"
                # expression_values.update(construct_expression_value(
                #     attribute_name, attribute_value, is_numeric=False))
                # expression_attribute_names.update(
                #     construct_expression_attribute_name(attribute_name))
            elif keyword:
                attribute_name = 'keywordsText'
                comparison_operator = 'contains'
                attribute_value = keyword.group(1).lower()
                result_string += " the keyword is " + attribute_value

                # Use a unique placeholder for each value
                placeholder_name = f"#{attribute_name}_{counter}"
                value_placeholder = f":{attribute_name}_{counter}"

                # filter_expressions.append(f"contains({placeholder_name}, {value_placeholder})")
                filter_expression += f"contains ({placeholder_name}, {value_placeholder})"
                expression_values.update(construct_expression_value(attribute_name + f"_{counter}", attribute_value, is_numeric=False))
                expression_attribute_names.update({placeholder_name: attribute_name})
            elif artist:
                attribute_name = 'artistSearch'
                comparison_operator = 'contains'
                attribute_value = expression.split(':', 1)[1].strip().lower()
                result_string += " the artist name includes " + attribute_value
                filter_expression += f"contains (#{attribute_name}, :{attribute_name})"
                expression_values.update(construct_expression_value(
                    attribute_name, attribute_value, is_numeric=False))
                expression_attribute_names.update(
                    construct_expression_attribute_name(attribute_name))
            elif card_set:
                attribute_name = 'setId'
                comparison_operator = '='
                attribute_value = expression.split(':', 1)[1].strip().upper()
                result_string += " the set is " + attribute_value
                # filter_expression += f"contains (#{attribute_name}, :{attribute_name})"
                value_placeholder = f":{attribute_name}_{counter}"
                filter_expression += f"#{attribute_name} = {value_placeholder}"
                expression_values[value_placeholder] = {'S': attribute_value}
                expression_attribute_names.update(
                    construct_expression_attribute_name(attribute_name))
            elif rotation:
                attribute_name = 'rotationSymbol'
                comparison_operator = '='
                attribute_value = expression.split(':', 1)[1].strip().upper()
                result_string += " the rotation symbol is " + attribute_value
                # filter_expression += f"contains (#{attribute_name}, :{attribute_name})"
                value_placeholder = f":{attribute_name}_{counter}"
                filter_expression += f"#{attribute_name} = {value_placeholder}"
                expression_values[value_placeholder] = {'S': attribute_value}
                expression_attribute_names.update(
                    construct_expression_attribute_name(attribute_name))
            elif format_legal or format_suspended:
                raw_format = expression.split(':', 1)[1].strip().lower()
                fmt_key = re.sub(r'[\s_]+', '', raw_format)
                if fmt_key in ('premier', 'p'):
                    attribute_name = 'legalPremier'
                    fmt_label = 'premier'
                elif fmt_key in ('eternal', 'e'):
                    attribute_name = 'legalEternal'
                    fmt_label = 'eternal'
                elif fmt_key in ('twinsuns', 'twin', 'ts'):
                    attribute_name = 'legalTwinSuns'
                    fmt_label = 'twin suns'
                else:
                    attribute_name = None
                    fmt_label = raw_format

                desired_status = 'suspended' if format_suspended else 'legal'
                result_string += f" the {fmt_label} format is {desired_status.replace('_', ' ')}"

                if attribute_name:
                    value_placeholder = f":{attribute_name}_{counter}"
                    filter_expression += f"#{attribute_name} = {value_placeholder}"
                    expression_values[value_placeholder] = {'S': desired_status}
                    expression_attribute_names.update(
                        construct_expression_attribute_name(attribute_name))
                else:
                    expression_attribute_names.update(
                        construct_expression_attribute_name('setId'))
                    filter_expression += "(attribute_exists(#setId) AND attribute_not_exists(#setId))"
            elif event:
                attribute_name = 'eventType'
                # Support both underscore and space forms (e.g., planetary_qualifier vs planetary qualifier)
                raw_val = expression.split(':', 1)[1].strip()
                av = raw_val.lower()
                av_space = av.replace('_', ' ')
                av_underscore = av.replace(' ', '_')
                pretty_val = av_space
                result_string += " the event is " + pretty_val
                # Use OR to match either stored form
                ph_space = f":{attribute_name}_{counter}_space"
                ph_underscore = f":{attribute_name}_{counter}_underscore"
                filter_expression += f"(#{attribute_name} = {ph_space} OR #{attribute_name} = {ph_underscore})"
                expression_values[ph_space] = {'S': av_space}
                expression_values[ph_underscore] = {'S': av_underscore}
                expression_attribute_names.update(
                    construct_expression_attribute_name(attribute_name))
            elif source:
                attribute_name = 'sourceSetId'
                comparison_operator = '='
                attribute_value = expression.split(':', 1)[1].strip().upper()
                result_string += " the source set is " + attribute_value
                filter_expression += f"#{attribute_name} = :{attribute_name}"
                expression_values.update(construct_expression_value(
                    attribute_name, attribute_value, is_numeric=False))
                expression_attribute_names.update(
                    construct_expression_attribute_name(attribute_name))
            elif season:
                attribute_name = 'season'
                raw_val = expression.split(':', 1)[1].strip()
                # Normalize to both 'sX' lower and 'SX' upper; include numeric fallback
                av_lower = raw_val.lower()
                av_upper = raw_val.upper()
                if not av_lower.startswith('s'):
                    av_lower_s = 's' + av_lower
                    av_upper_s = 'S' + av_upper
                else:
                    av_lower_s = av_lower
                    av_upper_s = av_upper
                result_string += " the season is " + av_lower_s
                ph_lower = f":{attribute_name}_{counter}_lower"
                ph_upper = f":{attribute_name}_{counter}_upper"
                parts = [f"#{attribute_name} = {ph_lower}", f"#{attribute_name} = {ph_upper}"]
                expression_values[ph_lower] = {'S': av_lower_s}
                expression_values[ph_upper] = {'S': av_upper_s}
                if raw_val.isdigit():
                    ph_num = f":{attribute_name}_{counter}_num"
                    parts.append(f"#{attribute_name} = {ph_num}")
                    expression_values[ph_num] = {'S': raw_val}
                filter_expression += '(' + ' OR '.join(parts) + ')'
                expression_attribute_names.update(
                    construct_expression_attribute_name(attribute_name))
            elif trait:
                attribute_name = 'traits'
                comparison_operator = 'contains'
                
                attribute_value = expression.split(':', 1)[1].strip().upper()
                result_string += " the traits include " + attribute_value
                attribute_placeholder = attribute_name + '_' + attribute_value
                attribute_placeholder = re.sub(r'[ "\']', '_', attribute_placeholder)


                filter_expression += f"contains ({attribute_name}, :{attribute_placeholder})"
                expression_values.update(construct_expression_value(
                    attribute_placeholder, attribute_value, is_numeric=False))
            elif type:
                attribute_name = 'type'
                attribute_value = expression.split(':', 1)[1].strip().lower().title()
                result_string += " the type includes " + attribute_value
                attribute_placeholder = attribute_name + '_' + attribute_value
                attribute_placeholder = re.sub(r'[ "\']', '_', attribute_placeholder)
                comparison_operator = 'contains'
                filter_expression += f"contains (#{attribute_name}, :{attribute_placeholder})"
                
                expression_values.update(construct_expression_value(
                    attribute_placeholder, attribute_value, is_numeric=False))
                expression_attribute_names.update(
                    construct_expression_attribute_name(attribute_name))
            elif arena:
                attribute_name = 'arenas'
                comparison_operator = 'contains'
                
                attribute_value = expression.split(':', 1)[1].strip().upper().title()
                result_string += " the arena includes " + attribute_value
                attribute_placeholder = attribute_name + '_' + attribute_value
                attribute_placeholder = re.sub(r'[ "\']', '_', attribute_placeholder)


                filter_expression += f"contains ({attribute_name}, :{attribute_placeholder})"
                expression_values.update(construct_expression_value(
                    attribute_placeholder, attribute_value, is_numeric=False))
            elif rarity:
                attribute_name = 'rarity'
                attribute_value = expression.split(':', 1)[1].strip().upper()
                result_string += " the rarity includes " + attribute_value
                attribute_placeholder = attribute_name + '_' + attribute_value
                attribute_placeholder = re.sub(r'[ "\']', '_', attribute_placeholder)
                comparison_operator = 'contains'
                filter_expression += f"contains (#{attribute_name}, :{attribute_placeholder})"
                
                expression_values.update(construct_expression_value(
                    attribute_placeholder, attribute_value, is_numeric=False))
                expression_attribute_names.update(
                    construct_expression_attribute_name(attribute_name))
            elif variant:
                attribute_name = 'variantType'
                raw_variant = expression.split(':', 1)[1].strip()
                variant_key = re.sub(r'[\s_-]+', '', raw_variant.lower())

                # Include variants in results when variant: is present, even if variant: isn't the final token.
                include_all = True

                if variant_key in ("a", "all"):
                    result_string += " the variant is all"
                    continue

                variant_map = {
                    'h': 'Hyperspace',
                    'f': 'Foil',
                    'hf': 'Hyperspace Foil',
                    's': 'Showcase',
                    'p': 'Prestige',
                    'pf': 'Prestige Foil',
                    'ps': 'Prestige Serialized',
                    # Backwards-compatible aliases (older single-letter modes)
                    'y': 'Hyperspace Foil',
                    'r': 'Prestige Foil',
                    'e': 'Prestige Serialized',
                    # Full-word aliases
                    'hyperspace': 'Hyperspace',
                    'foil': 'Foil',
                    'hyperspacefoil': 'Hyperspace Foil',
                    'showcase': 'Showcase',
                    'prestige': 'Prestige',
                    'prestigefoil': 'Prestige Foil',
                    'prestigeserialized': 'Prestige Serialized',
                }

                attribute_value = variant_map.get(variant_key) or raw_variant.replace('_', ' ').replace('-', ' ').title()
                result_string += " the variant is " + attribute_value

                value_placeholder = f":{attribute_name}_{counter}"
                filter_expression += f"#{attribute_name} = {value_placeholder}"
                expression_values[value_placeholder] = {'S': attribute_value}
                expression_attribute_names.update(
                    construct_expression_attribute_name(attribute_name))
            elif name:
                attribute_name = 'searchName'
                comparison_operator = 'contains'
                attribute_value = expression.split(':', 1)[1].strip().lower()
                result_string += " the name includes " + attribute_value
                filter_expression += f"contains (#{attribute_name}, :{attribute_name})"
                expression_values.update(construct_expression_value(
                    attribute_name, attribute_value, is_numeric=False))
                expression_attribute_names.update(
                    construct_expression_attribute_name(attribute_name))
            else:
                attribute_name = 'searchName'
                # attribute_placeholder = attribute_name + '_' + expression
                # attribute_placeholder = re.sub(r'[ "\']', '_', attribute_placeholder)
                comparison_operator = 'contains'
                attribute_value = expression.lower()
                result_string += " the name includes " + attribute_value
                # filter_expression += f"contains (#{attribute_name}, :{attribute_placeholder})"
                filter_expression += f"contains (#{attribute_name}, :{attribute_name})"
                
                # expression_values.update(construct_expression_value(
                #     attribute_placeholder, attribute_value, is_numeric=False))
                expression_values.update(construct_expression_value(
                    attribute_name, attribute_value, is_numeric=False))
                expression_attribute_names.update(
                    construct_expression_attribute_name(attribute_name))

        if negated and filter_expression:
            filter_expression = f"NOT ({filter_expression})"

        for x in range(parentheses_removed):
            filter_expression += ')'
            result_string += ' )'
        filter_expressions.append(filter_expression)
        current_group.append(filter_expression)

    if current_group:
        filter_expression_groups.append(' AND '.join(current_group))

    filter_expression = ' OR '.join(filter_expression_groups)

    items = []
    scan_kwargs = {
        'TableName': 'Cards3'
    }

    if not expression_values:
        if not include_variants and not variant and include_all == False:
            filter_expression += "attribute_not_exists(isVariant) "
        if filter_expression:
            scan_kwargs['FilterExpression'] = filter_expression
    elif not expression_attribute_names:
        if not include_variants and not variant and include_all == False:
            filter_expression += " AND attribute_not_exists(isVariant) "
            print(filter_expression)
        scan_kwargs['FilterExpression'] = filter_expression
        scan_kwargs['ExpressionAttributeValues'] = expression_values
        print(scan_kwargs)
    else:
        if include_variants == False and not variant and include_all == False:
            filter_expression += " AND attribute_not_exists(isVariant) "
        print(filter_expression)
        scan_kwargs['FilterExpression'] = filter_expression
        scan_kwargs['ExpressionAttributeValues'] = expression_values
        scan_kwargs['ExpressionAttributeNames'] = expression_attribute_names
        print(scan_kwargs)

    while True:
        response = dynamodb.scan(**scan_kwargs)
        items.extend(response.get('Items', []))

        if 'LastEvaluatedKey' not in response:
            break

        scan_kwargs['ExclusiveStartKey'] = response['LastEvaluatedKey']
    # if not expression_values:
    #     if not include_variants and not variant and include_all == False:
    #         filter_expression += f"attribute_not_exists(isVariant) "
    #     if not filter_expression:
    #         response = dynamodb.scan(
    #             TableName=dynamodb_table
    #         )
    #     else:
    #         response = dynamodb.scan(
    #             TableName=dynamodb_table,
    #             FilterExpression=filter_expression
    #         )
    # elif not expression_attribute_names:
    #     if not include_variants and not variant and include_all == False:
    #         filter_expression += f" AND attribute_not_exists(isVariant) "
    #     response = dynamodb.scan(
    #         TableName=dynamodb_table,
    #         FilterExpression=filter_expression,
    #         ExpressionAttributeValues=expression_values
    #     )
    # else:
    #     # Execute the query and retrieve the matching items
    #     # print(filter_expression)
    #     if not include_variants and not variant and include_all == False:
    #         filter_expression += f" AND attribute_not_exists(isVariant) "

    #     response = dynamodb.scan(
    #         TableName=dynamodb_table,
    #         FilterExpression=filter_expression,
    #         ExpressionAttributeValues=expression_values,
    #         ExpressionAttributeNames=expression_attribute_names
    #     )

    # Process the response and extract the matching cards
    cards = process_response(items)
    if leader and base:
        set_card = leader.split('-')
        set_id = set_card[0]
        card_number = set_card[1]
        leader_card = get_card(set_id, card_number)

        set_card = base.split('-')
        set_id = set_card[0]
        card_number = set_card[1]

        base_card = get_card(set_id, card_number)

        l_aspects = leader_card['aspects']
        b_aspects = base_card['aspects']
        leader_base_aspects = l_aspects + b_aspects
        leader_base_counts = Counter(leader_base_aspects)

        for card in cards:
            if card['type'] in ('Leader', 'Base'):
                card['penalty'] = 'N/A'
                continue
            
            aspects = card['aspects']
            aspect_counts = Counter(aspects)
            
            penalty = 0
            for aspect, count in aspect_counts.items():
                if leader_base_counts[aspect] < count:
                    penalty += 2 * (count - leader_base_counts[aspect])

            # Add the 'penalty' value to the card
            card['penalty'] = penalty
    else:
        leader_card = None
        base_card = None
    # Determine the number of matching cards
    num_cards = len(cards)

    # Extract the search expressions from the search input
    search_expressions = []

    # Generate the sentence describing the search results
    search_description = f"{num_cards} {'card' if num_cards == 1 else 'cards'} where" + result_string
    search_expressions.append(search_input)

    reverse_order = sort_order == 'desc'
    if (sort_field == 'name'):
        sorted_cards = sorted(cards, key=lambda x: x.get(
            'name', 0), reverse=reverse_order)
    elif (sort_field in ['power', 'cost', 'hp']):
        # for card in cards:
        #     print(card['hp'])
        sorted_cards = sorted(cards, key=lambda x: int(
            x.get(sort_field, 0) or 0), reverse=reverse_order)
    elif (sort_field == 'setnumber' or sort_field == None):
        if reverse_order:
            sorted_cards = cards
            sorted_cards.reverse()
        else:
            sorted_cards = cards
            print("hle")
    elif (sort_field == 'type'):
        sorted_cards = sorted(cards, key=lambda x: x.get(
            'type', 0), reverse=reverse_order)
    elif (sort_field == 'rarity'):
        sorted_cards = sorted(cards, key=lambda x: x.get(
            'rarity', 0), reverse=reverse_order)
    elif (sort_field == 'traits'):
        sorted_cards = sorted(cards, key=lambda x: x.get(
            'traits', 0), reverse=reverse_order)
    elif (sort_field == 'aspects'):
        sorted_cards = sorted(cards, key=lambda x: x.get(
            'aspect_icons', 0), reverse=reverse_order)
    elif (sort_field == 'artist'):
        sorted_cards = sorted(cards, key=lambda x: x.get(
            'artist', 0), reverse=reverse_order)
    elif (sort_field == 'arenas'):
        sorted_cards = sorted(cards, key=lambda x: x.get(
            'arenas', 0), reverse=reverse_order)
    elif (sort_field == 'penalty'):
        sorted_cards = sorted(cards, key=lambda x: float('inf') if x.get(
            'penalty') == 'N/A' else int(x.get('penalty', 0)), reverse=reverse_order)
    else:
        sorted_cards = cards
    return sorted_cards, search_description, leader_card, base_card


# def parse_numerical_expression(expression):
#     # Use regular expressions to extract attribute name, comparison operator, and value
#     match = re.match(r'([pchaPCHA])((?:<=|>=|<|>|=|!=|:)?)(\w+)', expression)
#     attribute_name = match.group(1).lower()
#     comparison_operator = match.group(2)
#     attribute_value = match.group(3)
#     if comparison_operator == '!=':
#         comparison_operator = '<>'
#     return attribute_name, comparison_operator, attribute_value

def parse_numerical_expression(expression):
    # Define allowed attribute names, sorted by length (longest first)
    allowed_attributes = ["pc", "up", "uh", "c", "h", "p", "a"]
    
    # Construct regex dynamically with sorted attributes
    attribute_pattern = r'\b(' + '|'.join(allowed_attributes) + r')\b'
    regex_pattern = rf'^({"|".join(allowed_attributes)})\s*(<=|>=|<|>|=|!=|:)\s*(\w+)$'
    
    # Match using regex
    match = re.match(regex_pattern, expression, re.IGNORECASE)
    
    if not match:
        raise ValueError("Invalid expression format")
    
    attribute_name = match.group(1).lower()
    comparison_operator = match.group(2)
    attribute_value = match.group(3)

    print("attribute_name ", attribute_name)
    print("comparison_operator ", comparison_operator)
    print("attribute_value ", attribute_value)

    if comparison_operator == '!=':
        comparison_operator = '<>'

    return attribute_name, comparison_operator, attribute_value

def construct_filter_expression(attribute_name, comparison_operator):
    # Construct the filter expression based on the attribute name and comparison operator
    return f'#{attribute_name} {comparison_operator} :value_{attribute_name}'


def construct_expression_value(attribute_name, attribute_value, is_numeric=True):
    expression_value = {}

    if is_numeric:
        # Assuming numeric attribute
        return {f':value_{attribute_name}': {'N': attribute_value}}
    else:
        expression_value[f":{attribute_name}"] = {'S': attribute_value}

    return expression_value


def construct_expression_attribute_name(attribute_name):
    # Construct the expression attribute name based on the attribute name
    return {f'#{attribute_name}': attribute_name}


def process_response(items):
    # Process the DynamoDB response and extract the matching cards
    # items = response['Items']
    # print("Items:\n")
    # print(items)
    set_info = dynamodb.scan(
            TableName='Sets',
        )
    cards = [process_item(item, set_info['Items']) for item in items]
    
    # max_element = set_info['Items'][0]["maxElement"]['S']
    # set_name = set_info['Items'][0]['fullName'][]

    # print(set_info['Items'])
    allVariants = []
    # for item in items:
    #     print("\nItem:\n")
    #     print(item)
    #     if 'variantCardNumbers' in item:
    #         variants = item.get('variantCardNumbers', {}).get('SS', [])
    #         for variant in variants:
    #             response = dynamodb.query(
    #                 TableName=dynamodb_table,
    #                 KeyConditionExpression='setId = :set_id and cardNumber = :card_number',
    #                 ExpressionAttributeValues={
    #                     ':set_id': {'S': item['setId']['S']},
    #                     ':card_number': {'S': variant}
    #                 }
    #             )
    #         if 'Items' in response:
    #             item2 = response['Items'][0]
    #             new_card = process_item(item2)
    #             cards.append(new_card)
    # #         print(variants)
    # #         allVariants.extend(variants)
    # # print(allVariants)
    
    return cards


def process_item(item, set_info = None):
    # Process a single item from the DynamoDB response and return a card object
    # Extract the necessary attributes from the item
   
    number = item['cardNumber']['S']
    artist = item.get('artist', {}).get('S', None)
    variant_type = item.get('variantType', {}).get('S', 'Original')
    rotation_symbol = item.get('rotationSymbol', {}).get('S', None)
    legal_premier = item.get('legalPremier', {}).get('S', None)
    legal_eternal = item.get('legalEternal', {}).get('S', None)
    legal_twin_suns = item.get('legalTwinSuns', {}).get('S', None)
    card_set = item['setId']['S']
    card_id = item.get('cardId', {}).get('S') or f"{card_set}-{number}"
    base_card_id = item.get('baseCardId', {}).get('S') or card_id

    front_art = 'https://cdn.swu-db.com/images/cards/' + card_set + '/' + number.rstrip("F") + '.png' 

    display_price = item.get('displayPrice', {}).get('N', 0)
    url = item.get('url', {}).get('S', None)
    tcg_product_id = item.get('tcgplayerId', {}).get('S', None)
    
    type = item['type']['S']

    if not set_info:
        set_info = dynamodb.query(
                TableName='Sets',
                KeyConditionExpression='setId = :set_id',
                ExpressionAttributeValues={
                    ':set_id': {'S': card_set}
                }
            )
        max_element = set_info['Items'][0]["maxElement"]['S']
        set_name = set_info['Items'][0]['fullName']['S']
    else:
        matching_element = next((element for element in set_info if element['setId']['S'] == card_set), None)
        max_element = matching_element['maxElement']['S']
        set_name = matching_element['fullName']['S']
    
    rarity = item['rarity']['S']

    if rarity == 'C':
        rarity = "Common"
    elif rarity == 'U':
        rarity = "Uncommon"
    elif rarity == 'R':
        rarity = "Rare"
    elif rarity == 'L':
        rarity = "Legendary"
    elif rarity == 'S':
        rarity = "Special"
    
    
    has_back = item['hasBack']['BOOL']
    if has_back:
        back_art = 'https://cdn.swu-db.com/images/cards/' + card_set + '/' + number.rstrip("F") + '-b.png'
    else:
        back_art = None
    power = item.get('printedPower', {}).get('S', None)
    if power == None:
        power = item.get('power', {}).get('N', None)
    subtitle = item.get('subtitle', {}).get('S', None)
    text = item.get('textStyled', {}).get('S', None)
    cost = item.get('cost', {}).get('N', None)
    hp = item.get('printedHP', {}).get('S', None)
    number_display = item.get('cardNumberDisplay', {}).get('S', None)
    if hp == None:
        hp = item.get('HP', {}).get('N', None)
    upgrade_power = item.get('upgradePowerDisplay', {}).get('S', None)
    upgrade_hp = item.get('upgradeHPDisplay', {}).get('S', None)
    raw_name = item['name']['S']
    name = raw_name
    # back_art = item.get('backArt', {}).get('S', None)
    # artist = item.get('artist', {}).get('S', None)
    is_landscape = item.get('isLandscape', {}).get('BOOL', False)

    if is_landscape:
        v_front_art = 'https://cdn.swu-db.com/images/cards/' + card_set + '/' + number.rstrip("F") + '-r.png'
    else:
        v_front_art = None
    aspect_icons = []
    aspects_response = item.get('aspects', {}).get('L', [])
    aspects = [aspect['S'] for aspect in aspects_response]
    epic_action = item.get('epicActionStyled', {}).get('S', None)
    back_text = item.get('backTextStyled', {}).get('S', None)
    is_unique = item.get('isUnique', {}).get('BOOL', False)

    traits_response = item.get('traits', {}).get('L', [])
    traits = [traits['S'] for traits in traits_response]
    arenas = item.get('arenas', {}).get('SS', [])
    

    for aspect in aspects:
        aspect = aspect.lower()
        # Assuming aspect icons are named after their respective aspect names
        aspect_icon_path = f'/static/images/{aspect}.png'
        aspect_icons.append(aspect_icon_path)

    if subtitle is not None:
        name = raw_name + ' - ' + subtitle

    # Create and return a card object
    card = {
        'set': card_set,
        'number': number,
        'front_art': front_art,
        'has_back': has_back,
        'back_art': back_art,
        'power': power,
        'name': name,
        'cost': cost,
        'hp': hp,
        'type': type,
        'rarity': rarity,
        'subtitle': subtitle,
        'is_landscape': is_landscape,
        'v_front_art': v_front_art,
        'aspect_icons': aspect_icons,
        'traits': traits,
        'artist': artist,
        'text': text,
        'arenas': arenas,
        'epic_action': epic_action,
        'back_text': back_text,
        'aspects': aspects,
        'is_unique': is_unique,
        'variants': [],
        'card_id': card_id,
        'base_card_id': base_card_id,
        'variant_type': variant_type,
        'rotation_symbol': rotation_symbol,
        'legal_premier': legal_premier,
        'legal_eternal': legal_eternal,
        'legal_twin_suns': legal_twin_suns,
        'max_element': max_element,
        'set_name': set_name,
        'display_price': float(display_price),
        'url': url,
        'tcg_product_id': tcg_product_id,
        'upgrade_power': upgrade_power,
        'upgrade_hp': upgrade_hp,
        'number_display': number_display
    }
    return card


@app.route('/', methods=['GET'])
def homepage():
    return render_template('index.html')


@app.route('/search', methods=['GET', 'POST'])
def search():
    search_input = request.args.get('q', '')
    if not search_input or not search_input.strip():
        return redirect(url_for('homepage'))
    search_input = search_input.replace('“', '"').replace('”', '"')
    sort_field = request.args.get('sort')
    sort_order = request.args.get('sortOrder')
    display_mode = request.args.get('display_mode')
    variant_mode = request.args.get('variant_mode')
    leader = request.args.get('leader')
    base = request.args.get('base')
    variants = request.args.get('variants')
    if variants and variants.upper() == 'TRUE':
        variants = True
    else:
        variants = False
    # print("variants: " + variants)
    cards, result_string, leader, base = search_cards(search_input, sort_field, sort_order, leader, base, variants)
    for card in cards:
        card.pop('back_text', None)
    # cards_json = json.dumps(cards, ensure_ascii=False, default=lambda x: None)
    # Pass the cards data to the template for rendering
    return render_template('search_results.html', cards=cards, result_string=result_string, sort_field=sort_field, sort_order=sort_order, q=search_input, display_mode=display_mode, leader=leader, base=base, variant_mode=variant_mode)


# @app.route('/card/<string:set>/<string:number>/<string:name>')
# def card(set, number, name):
#     # Retrieve card information based on the set, number, and name
#     # Render the card page template with the retrieved card information
#     print(number)
#     my_card = get_card(set, number)
#     next_card = get_next_card(set, number)
#     prev_card = get_previous_card(set, number)
#     variants = get_variants(my_card["variants"])
#     return render_template('card.html', set=set, number=number, name=name, card=my_card, next_card=next_card, prev_card=prev_card, variants=variants)

@app.route('/card/<string:set>/<string:number>')
def card(set, number):
    # Retrieve card information based on the set, number, and name
    # Render the card page template with the retrieved card information
    print(number)
    my_card = get_card(set, number)
    my_card['price_url'] = get_price_url(my_card.get('tcg_product_id'))
    next_card = get_next_card(set, number)
    prev_card = get_previous_card(set, number)
    variants = get_variants(my_card["base_card_id"], my_card["card_id"])
    return render_template('card.html', set=set, number=number, name=my_card['name'], card=my_card, next_card=next_card, prev_card=prev_card, variants=variants)

@app.route('/submit-feedback', methods=['POST'])
def submit_feedback():
    message = request.form.get('message')

    # Process the feedback data, e.g., publish to SNS
    publish_feedback_to_sns(message)

    # Flash a success message
    flash('Your feedback has been submitted successfully!', 'success')

    # Redirect to the homepage after successful submission
    return redirect(url_for('homepage'))

@app.route('/syntax')
def syntax():
    return render_template('syntax.html')

@app.route('/api')
def api():
    return render_template('api.html')


@app.route('/feedback')
def feedback():
    return render_template('feedback.html')

@app.route('/resources')
def resources():
    return render_template('resources.html')

@app.route('/sets')
def sets_list():
    # Retrieve all sets from DynamoDB and render a page listing them
    response = dynamodb.scan(
        TableName='Sets'
    )

    # Build set objects and index by id
    sets = []
    by_id = {}
    for item in response.get('Items', []):
        set_id = item.get('setId', {}).get('S')
        if not set_id:
            continue
        full_name = item.get('fullName', {}).get('S', set_id)
        max_element = item.get('maxElement', {}).get('S')
        # Prefer an explicit number of cards if present
        number_cards = None
        if 'numberCards' in item:
            number_cards = item.get('numberCards', {}).get('N') or item.get('numberCards', {}).get('S')
        # Fallback to max_element when numberCards is missing
        cards_count = number_cards or max_element
        release_date = item.get('releaseDate', {}).get('S') if 'releaseDate' in item else None
        parent_id = item.get('parentSetId', {}).get('S') if 'parentSetId' in item else None

        s = {
            'id': set_id,
            'name': full_name,
            'max_element': max_element,
            'cards_count': cards_count,
            'release_date': release_date,
            'parent_id': parent_id
        }
        sets.append(s)
        by_id[set_id] = s

    # Heuristic: OP subsets (e.g., sorop) are children of base (e.g., sor) if not explicitly specified
    for s in sets:
        if not s.get('parent_id') and s['id'].endswith('op'):
            base = s['id'][:-2]
            if base in by_id:
                s['parent_id'] = base

    # Build groups: parents with children
    children_map = {}
    for s in sets:
        pid = s.get('parent_id')
        if pid:
            children_map.setdefault(pid, []).append(s)

    parents = [s for s in sets if not s.get('parent_id')]

    # Sort parents by release_date then name; sort children by release_date then name
    def sort_key(x):
        return (x.get('release_date') is None, x.get('release_date') or x.get('name'))

    parents.sort(key=sort_key)
    for pid, kids in children_map.items():
        kids.sort(key=sort_key)

    # Synthesize children under promo year sets (e.g., P25) grouped by eventType + sourceSetId
    promo_parents = [p for p in parents if re.match(r'^P\d{2}$', p['id'] or '', re.IGNORECASE)]
    for promo in promo_parents:
        promo_code = promo['id']
        # Query all cards in this promo set
        query_kwargs = {
            'TableName': dynamodb_table,
            'KeyConditionExpression': 'setId = :sid',
            'ExpressionAttributeValues': {':sid': {'S': promo_code}}
        }
        items = []
        while True:
            resp = dynamodb.query(**query_kwargs)
            items.extend(resp.get('Items', []))
            if 'LastEvaluatedKey' not in resp:
                break
            query_kwargs['ExclusiveStartKey'] = resp['LastEvaluatedKey']

        # Group by eventType + sourceSetId
        groups_map = {}
        for it in items:
            evt = it.get('eventType', {}).get('S') if 'eventType' in it else None
            src = it.get('sourceSetId', {}).get('S') if 'sourceSetId' in it else None
            if not evt or not src:
                continue
            key = (evt.lower(), src.upper())
            groups_map[key] = groups_map.get(key, 0) + 1

        promo_children = []
        for (evt, src), count in groups_map.items():
            src_name = by_id.get(src, {}).get('name', src)
            # Pretty event type label for display
            pretty_evt = ' '.join([w.capitalize() for w in evt.replace('_', ' ').split()])
            child_name = f"{src_name} — {pretty_evt} Promos"
            # Use a token-safe form for event (underscores, lowercase)
            evt_token = evt.replace(' ', '_').lower()
            link = f"/search?q=set%3A{promo_code.lower()}+and+event:{evt_token}+and+source:{src.lower()}&variants=true"
            promo_children.append({
                'id': promo_code,
                'name': child_name,
                'cards_count': str(count),
                'release_date': None,
                'parent_id': promo_code,
                'link': link
            })

            # Also duplicate this promo subset under the base set (e.g., SEC)
            base_children = children_map.get(src, [])
            base_children.append({
                'id': promo_code,
                'name': child_name,
                'cards_count': str(count),
                'release_date': None,
                'parent_id': src,
                'link': link
            })
            children_map[src] = base_children

        # Additionally, create SQ (Sector Qualifier) groupings by season under the promo parent
        sq_by_season = {}
        for it in items:
            evt = it.get('eventType', {}).get('S') if 'eventType' in it else None
            if not evt or evt.lower() != 'sq':
                continue
            season_val = it.get('season', {}).get('S') if 'season' in it else None
            if not season_val:
                continue
            # Normalize season to lowercase 'sX'
            sv = season_val.lower()
            if not sv.startswith('s'):
                sv = f's{sv}'
            sq_by_season[sv] = sq_by_season.get(sv, 0) + 1

        for sv, count in sq_by_season.items():
            # Pretty label: Season X
            season_display = sv[1:] if sv.startswith('s') else sv
            child_name = f"Sector Qualifier — Season {season_display}"
            link = f"/search?q=set%3A{promo_code.lower()}+and+event:sq+and+season:{sv}&variants=true"
            promo_children.append({
                'id': promo_code,
                'name': child_name,
                'cards_count': str(count),
                'release_date': None,
                'parent_id': promo_code,
                'link': link
            })

        # Create RQ (Regional Qualifier) groupings by season
        rq_by_season = {}
        for it in items:
            evt = it.get('eventType', {}).get('S') if 'eventType' in it else None
            if not evt or evt.lower() != 'rq':
                continue
            season_val = it.get('season', {}).get('S') if 'season' in it else None
            if not season_val:
                continue
            sv = season_val.lower()
            if not sv.startswith('s'):
                sv = f's{sv}'
            rq_by_season[sv] = rq_by_season.get(sv, 0) + 1

        for sv, count in rq_by_season.items():
            season_display = sv[1:] if sv.startswith('s') else sv
            child_name = f"Regional Qualifier — Season {season_display}"
            link = f"/search?q=set%3A{promo_code.lower()}+and+event:rq+and+season:{sv}&variants=true"
            promo_children.append({
                'id': promo_code,
                'name': child_name,
                'cards_count': str(count),
                'release_date': None,
                'parent_id': promo_code,
                'link': link
            })

        # Create GC (Galactic Championship) groupings by season
        gc_by_season = {}
        for it in items:
            evt = it.get('eventType', {}).get('S') if 'eventType' in it else None
            if not evt or evt.lower() != 'gc':
                continue
            season_val = it.get('season', {}).get('S') if 'season' in it else None
            if not season_val:
                continue
            sv = season_val.lower()
            if not sv.startswith('s'):
                sv = f's{sv}'
            gc_by_season[sv] = gc_by_season.get(sv, 0) + 1

        for sv, count in gc_by_season.items():
            season_display = sv[1:] if sv.startswith('s') else sv
            child_name = f"Galactic Championship — Season {season_display}"
            link = f"/search?q=set%3A{promo_code.lower()}+and+event:gc+and+season:{sv}&variants=true"
            promo_children.append({
                'id': promo_code,
                'name': child_name,
                'cards_count': str(count),
                'release_date': None,
                'parent_id': promo_code,
                'link': link
            })

        if promo_children:
            promo_children.sort(key=lambda x: (x['name']))
            existing = children_map.get(promo_code, [])
            children_map[promo_code] = existing + promo_children

    # Ensure all child lists are sorted after adding synthetic promo links
    for pid, kids in children_map.items():
        try:
            kids.sort(key=sort_key)
        except Exception:
            # Fallback sort by name if structure differs
            kids.sort(key=lambda x: x.get('name', ''))

    groups = [{
        'parent': p,
        'children': children_map.get(p['id'], [])
    } for p in parents]

    return render_template('sets.html', groups=groups)

@app.route('/advanced')
def advanced():
    response = dynamodb.scan(
        TableName=dynamodb_table
    )

    # Retrieve unique traits from the items
    unique_traits = set('')
    unique_types = set('')
    leaders = []
    bases = []
    for item in response['Items']:
        if 'traits' in item:
            traits_list = item['traits']['L']
            traits = [traits['S'] for traits in traits_list]
            unique_traits.update(traits)
        if 'type' in item:
            type_list = item['type']['S']
            unique_types.add(type_list)

            if item['type'] == {'S': 'Leader'}:
                leader = {
                    'setId': item['setId']['S'],
                    'cardNumber': item['cardNumber']['S'],
                    'name': item['name']['S'],
                    'subtitle': item['subtitle']['S']
                }
                leaders.append(leader)
            elif item['type'] == {'S': 'Base'}:
                base = {
                    'setId': item['setId']['S'],
                    'cardNumber': item['cardNumber']['S'],
                    'name': item['name']['S']
                }
                bases.append(base)

    return render_template('advanced.html', unique_traits=sorted(unique_traits), leaders=leaders, bases=bases, unique_types=sorted(unique_types))

@app.route('/advanced_results', methods=['GET', 'POST'])
def advanced_results():
    aspects = request.form.getlist('aspect')
    aspect_opt = request.form.get('aspect-option')
    card_name = request.form.get('card-name')
    card_text = request.form.get('card-text')
    traits = request.form.getlist('trait[]')
    display_mode = request.form.get('display-option')
    sort_field = request.form.get('display-sort-column')
    stat_select_1 = request.form.get('stat-select-1')
    stat_select_2 = request.form.get('stat-select-2')
    stat_select_3 = request.form.get('stat-select-3')
    opeator_select_1 = request.form.get('operator-select-1')
    opeator_select_2 = request.form.get('operator-select-2')
    opeator_select_3 = request.form.get('operator-select-3')
    value_input_1 = request.form.get('value-input-1')
    value_input_2 = request.form.get('value-input-2')
    value_input_3 = request.form.get('value-input-3')
    chosen_leader = request.form.get('leader')
    chosen_base = request.form.get('base')
    partial_match = request.form.get('partial-match')
    arena = request.form.get('arena')
    artist = request.form.get('artist')
    rarities = request.form.getlist('rarity')

    traits_list = []
    types_list = []
    # print(traits_list)

    for string in traits:
        if string.isupper():
            traits_list.append(string)
        elif string != '':
            types_list.append(string)


    search_input = ''
    if aspects:
        search_input = 'a' + aspect_opt + ''.join(aspects)
    if artist:
        search_input += ' artist:' + artist
    if rarities:
        search_input += ' (r:' + ' OR r:'.join(rarities)  + ' )'
    if card_name:
        search_input += ' ' + card_name
    if arena:
        search_input += ' arena:' + arena
    if traits_list or types_list:
        if partial_match == 'on':
            search_input += ' ('
            count = 0
            if traits_list:
                for trait in traits_list:
                    if count > 0:
                        search_input += ' or tr:"' + trait + '"'
                    else:
                        search_input += ' tr:"' + trait + '"'
                    count += 1
            if types_list:
                for type in types_list:
                    if count > 0:
                        search_input += ' or type:' + type
                    else:
                        search_input += ' type:' + type
                    count += 1
            search_input += ' )'
        else:

            if traits_list:
                for trait in traits_list:
                    search_input += ' tr:"' + trait + '"'
            if types_list:
                for type in types_list:
                    search_input += ' type:' + type

    if card_text:
        search_input += ' t:' + card_text
    if value_input_1:
        search_input += ' ' + stat_select_1 + opeator_select_1 + value_input_1
    if value_input_2:
        search_input += ' ' + stat_select_2 + opeator_select_2 + value_input_2
    if value_input_3:
        search_input += ' ' + stat_select_3 + opeator_select_3 + value_input_3

    sort_order = 'asc'
    return redirect(url_for('search', q=search_input, sort=sort_field, sort_order=sort_order, display_mode=display_mode, leader=chosen_leader, base=chosen_base))

@app.template_filter('replace_aspects')
def replace_aspects(text):
    aspect_icons = {
        'Heroism': 'heroism.png',
        'Vigilance': 'vigilance.png',
        'Villainy': 'villainy.png',
        'Command': 'command.png',
        'Cunning': 'cunning.png',
        'Aggression': 'aggression.png',
        'Exhaust': 'exhaust.png',
    }

    for aspect, icon_filename in aspect_icons.items():
        placeholder = '{{' + aspect + '}}'
        icon_path = url_for('static', filename='images/' + icon_filename)
        text = text.replace(
            placeholder, f'<span class="aspect-icon"><img src="{icon_path}" alt="{aspect} icon"></span>')

    for i in range(0, 10):  # This will go from 1 to 9
        icon_path = url_for('static', filename=f'images/cost{i}.png')
        text = text.replace(f'{{C={i}}}', f'<span class="aspect-icon"><img src="{icon_path}" alt="cost{i} icon"></span>')


    keywords = ['Smuggle', 'Bounties', 'Ambush', 'Bounty', 'Overwhelm', 'Sentinel', 'Shielded', 'Raid 3', 'Saboteur', 'Grit',
    'Restore 2', 'Restore 1', 'Raid 2', 'Exploit 2', 'Coordinate', 'Exploit 1', 'Exploit 3', 'Exploit 4', 'Raid 1', 'Restore 3', 'Piloting', 'Keywords', 'Keyword', 'Hidden',
    'Raid', 'Restore', 'Restore 4', 'Raid 4', 'Plot']

    for keyword in keywords:
        placeholder = '{' + keyword + '}'
        text = text.replace(placeholder, f'<span class="keyword-text"><b>{keyword}</b></span>')


    # Define a function to replace the placeholder
    def replace_power_placeholder(match):
        # Extract the power value from the match
        power = match.group(1)
        # Return the replacement text
        return f'<span class="red-text">{power}</span>'

    # Define a function to replace the placeholder
    def replace_hp_placeholder(match):
        # Extract the power value from the match
        power = match.group(1)
        # Return the replacement text
        return f'<span class="blue-text">{power}</span>'
    
    def replace_match(match):
        trait = match.group(1)
        return f'<b><i><a href="/search?q=trait%3A\'{trait}\'" class="trait-link">{trait}</a></i></b>'

    pattern = re.compile(r'\{([+-]?\d+)p\}')
    text = pattern.sub(replace_power_placeholder, text)

    pattern = re.compile(r'\{([+-]?\d+)h\}')
    text = pattern.sub(replace_hp_placeholder, text)

    pattern = r"<b><i>(.*?)</i></b>"
    text = re.sub(pattern, replace_match, text)
    
    return Markup(text)

@app.route('/get_prices', methods=['GET'])
def get_prices():
    # Get tcg_product_id from request
    tcg_product_id = request.args.get('tcg_product_id')

    # Query DynamoDB for prices
    response = dynamodb.query(
        TableName='Prices',
        KeyConditionExpression='productId = :pid',
        ExpressionAttributeValues={
            ':pid': {'S': tcg_product_id}
        }
    )

    # Extract relevant data from DynamoDB response
    prices = []
    for item in response['Items']:
        price_entry = {
            'subTypeName': item.get('subTypeName', {}).get('S', ''),
            'market': item.get('marketPrice', {}).get('N', ''),
            'low': item.get('lowPrice', {}).get('N', ''),
            'mid': item.get('midPrice', {}).get('N', ''),
            'high': item.get('highPrice', {}).get('N', ''),
            'url': item.get('url', {}).get('S', '')
        }
        prices.append(price_entry)

    return jsonify(prices)

if __name__ == '__main__':
    app.run(debug=False)
