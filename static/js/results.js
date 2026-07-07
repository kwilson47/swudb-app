 
// function buildUpdatedVariantsURL(variantField, selectedDisplayMode) {
//   const currentURL = new URL(window.location.href);
//   let updatedURL;
//   let queryParams = new URLSearchParams(currentURL.search);

//   // Modify the 'q' parameter to append 'variant' parameter
//   let qParam = queryParams.get('q');
//   if (qParam) {
//     // Check if 'variant' already exists within 'q' parameter
//     const variantRegex = /variant:[^&+]+/g;
//     if (variantRegex.test(qParam)) {
//       if (variantField === 'n') {
//         // Remove 'variant' part entirely if 'n' is selected
//         qParam = qParam.replace(variantRegex, '').replace(/\+and\+$/, '');
//       } else {
//         // Replace existing 'variant' part with new value
//         qParam = qParam.replace(variantRegex, `variant:${variantField}`);
//       }
//     } else {
//       // Append 'variant' part to existing 'q' parameter
//       qParam += `+and+variant:${variantField}`;
//     }
//   } else {
//     // Set 'q' parameter with 'variant' part
//     qParam = `variant:${variantField}`;
//   }

//   queryParams.set('q', qParam);
//   queryParams.set('variants', variantField);
//   currentURL.search = decodeURIComponent(queryParams.toString());

//   return currentURL.toString();
// }

function buildUpdatedVariantsURL(variantField, selectedDisplayMode) {
  const currentURL = new URL(window.location.href);
  const baseURL = `${currentURL.origin}${currentURL.pathname}`;

  // Retrieve and clean up the query parameters
  let qParam = currentURL.searchParams.get('q');
  console.log("Initial qParam:", qParam);

  if (qParam) {
    // First, decode any URL encoding, so we can work with actual '+' signs
    qParam = decodeURIComponent(qParam);
    console.log("After decoding qParam:", qParam);

    // Remove the existing variant part from the qParam if it's there
    const variantRegex = /(?:\+and\+)?variant:[^&+]+/g;
    qParam = qParam.replace(variantRegex, '').trim();
    console.log("After variant removal:", qParam);

    // Remove any leftover '+and+' or 'and' (encoded and plain)
    qParam = qParam.replace(/(?:\+and\+|and)/g, '').trim();
    console.log("After cleanup of +and+:", qParam);

    // If variantField is 'n', just remove +and+ from qParam if it exists
    if (variantField === 'n') {
      qParam = qParam.replace(/(?:\+and\+|and)/g, '').trim();
      console.log("After removing +and+ due to 'n':", qParam);
    } else if (variantField !== 'n') {
      // Add the new variant if it's not 'n'
      if (qParam) {
        qParam += `+and+variant:${variantField}`;
      } else {
        qParam = `variant:${variantField}`;
      }
    }

    console.log("After adding variant:", qParam);
  } else if (variantField !== 'n') {
    qParam = `variant:${variantField}`;
  }

  // Construct the query string manually with + as the separator
  let queryParams = new URLSearchParams(currentURL.searchParams);
  if (qParam && qParam.trim()) {
    queryParams.set('q', qParam);
  } else {
    queryParams.delete('q');
  }

  queryParams.set('variants', variantField);

  // Manually encode the query string, leaving the '+' intact
  let queryString = queryParams.toString().replace(/%20/g, '+').replace(/%2B/g, '+');
  console.log("Manually encoded query string:", queryString);

  // Rebuild the URL with the updated query string
  const updatedURL = `${baseURL}?${queryString}`;
  console.log("Updated URL:", updatedURL);

  return updatedURL;
}















  
  
  
  var displayModeSelect = document.getElementById('view-mode-select');
  var variantModeSelect = document.getElementById('view-variants-select');
  // var cardTable = document.getElementById('cardTable');
  // var cardTable = document.getElementById('cardTable_wrapper');
  var cardGrid = document.getElementById('card-grid-container');

  variantModeSelect.addEventListener('change', function() {
    // Get the selected option value
    var selectedOption = variantModeSelect.options[variantModeSelect.selectedIndex];
    var selectedVariant = selectedOption.value;

    if (selectedVariant == 'hyperspace') {
      selectedVariant = 'h'
    }  else if (selectedVariant == 'foil') {
      selectedVariant = 'f'
    } else if (selectedVariant == 'showcase') {
      selectedVariant = 's'
    } else if (selectedVariant == 'prestige') {
      selectedVariant = 'p'
    } else if (selectedVariant == 'normal') {
      selectedVariant = 'n'
    } else if (selectedVariant == 'hyperspace-foil') {
      selectedVariant = 'y'
    } else if (selectedVariant == 'prestige-foil') {
      selectedVariant = 'r'
    } else if (selectedVariant == 'prestige-serialized') {
      selectedVariant = 'e'
    }
  
    // Build the updated URL
    var updatedURL = buildUpdatedVariantsURL(selectedVariant);
  
    // Redirect to the updated URL
    window.location.href = updatedURL;
  });
  
  function updateDisplay() {
    var cardTable = document.getElementById('cardTable_wrapper');
    var selectedOption = displayModeSelect.value;
  
    if (selectedOption === 'checklist') {
      var screenWidth = $(window).width();
      if (screenWidth < 1600) {
        $("#cardTable_wrapper").css("display", "block");
      } else {
        $("#cardTable_wrapper").css("display", "inline-table");
      }
      console.log(cardTable)
      // cardTable.style.display = 'inline-table';
      // var table = $('#cardTable').DataTable();
      // table.columns.adjust();
      // cardTable.removeAttribute("style");
      cardGrid.style.display = 'none';
    } else if (selectedOption === 'images') {
      console.log(cardTable)
      cardTable.style.display = 'none';
      cardGrid.style.display = 'flex';
    }
  
    // Get the current URL and search parameters
    var url = new URL(window.location.href);
    var params = new URLSearchParams(url.search);
  
    // Set the new display mode
    params.set('display_mode', selectedOption);
  
    // Update the URL with the new display mode
    url.search = params.toString();
    var newURL = url.toString();
  
    // Replace the current URL with the updated URL
    window.history.replaceState(null, null, newURL);
  
  }
  
  $(window).on("resize", function () {
    // Call the function to set the style based on screen width
    updateDisplay();
  });
  
  
  
  
  
  
  
  
  document.addEventListener('DOMContentLoaded', function () {
    // Get the table headers
    var tableHeaders = document.querySelectorAll('#cardTable th.sortable');
  
    // Add click event listener to each table header
    tableHeaders.forEach(function (header) {
      header.addEventListener('click', function () {
        var column = header.getAttribute('data-column');
        var sortSelect = document.getElementById('sort-select');
        var currentSortOrder = sortSelect.value;
        var sortOrderSelect = document.getElementById('sort-order-select');
        var currentSortOrderSelect = sortOrderSelect.value;
  
        // Determine the new sort direction based on user's action
        var newSortDirection;
        var selectedOption = displayModeSelect.value;
        if (column === currentSortOrder) {
          // If the user clicked on the current sort column, toggle the sort direction
          newSortDirection = currentSortOrder.startsWith('-') ? currentSortOrder.slice(1) : '-' + currentSortOrder;
          if (currentSortOrderSelect == 'asc') {
            sortOrderSelect.value = 'desc'
          } else {
            sortOrderSelect.value = 'asc'
          }
          if (selectedOption === 'Images') {
            sortOrderSelect.dispatchEvent(new Event('change'));
          }
            
        } else {
          // If the user clicked on a different sort column, use the default sort direction
          newSortDirection = column;
          sortSelect.value = newSortDirection;
          if (selectedOption === 'Images') {
            sortSelect.dispatchEvent(new Event('change'));
          }
          
        }
  
        // Update the sort order select and trigger the search
  
        // performSearch();
      });
    });
  
    if (displayModeSelect) {
      // Add event listener only if the element exists
      displayModeSelect.addEventListener('change', updateDisplay);
    
      // Get the value of the "display_mode" query parameter from the URL
      var searchParams = new URLSearchParams(window.location.search);
      var displayModeParam = searchParams.get('display_mode');
    
      // Set the value of the "displayMode" select element based on the query parameter
      if (displayModeParam) {
        displayModeSelect.value = displayModeParam;
      }
    
      // Call the updateDisplay function initially to apply the selected display mode
      // updateDisplay();
    }

    switch(searchParams.get('variants')){
      case 'f':
        variantModeSelect.value = 'foil';
        break;
      case 'n':
        variantModeSelect.value = 'normal';
        break;
      case 'h':
        variantModeSelect.value = 'hyperspace';
        break;
      case 'hf':
        variantModeSelect.value = 'hyperspace foil';
        break;
      case 's':
        variantModeSelect.value = 'showcase';
        break;
      case 'p':
        variantModeSelect.value = 'prestige';
        break;
      case 'r':
        variantModeSelect.value = 'prestige-foil';
        break;
      case 'e':
        variantModeSelect.value = 'prestige-serialized';
        break;
      case 'all':
        variantModeSelect.value = 'all';
        break;
    }
    

    //Hide the image when the page loads
    var cardImages = document.querySelectorAll('.hover-card-image');
    cardImages.forEach(function (cardImage) {
      cardImage.style.display = 'none';
    });
  
    // Hide the image when the back button is clicked
    window.addEventListener('pageshow', function (event) {
      if (event.persisted) {
        cardImages.forEach(function (cardImage) {
          cardImage.style.display = 'none';
        });
      }
    });
  });
  
  $(document).ready(function () {
    var myDataTable = $('#cardTable').DataTable({
      "pageLength": 50,
      "language": {
        "search": "Filter results:"
      },
      "order": [[1, 'asc']],
      "scrollX": true,
      'aoColumnDefs': [ 
    // {
    //     targets: 1,
    //     render: function (data, type, row) {
    //       if (type === 'type' || type === 'sort') {
    //         if (data === 'T01') {
    //           return 253;  // Some arbitrary high number
    //         }
    //         if (data === 'T02') {
    //             return 254;  // Some arbitrary high number
    //           }
    //         return data;  // Numeric value
    //       }
    //       return data;  // return teh data for the other orthognal types
    //     }
    //   },
      {
        targets: [6, 7, 8],
        render: function (data, type, row) {
          if (type === 'type' || type === 'sort') {
              // Check if the data starts with a "+" or "-"
              if (typeof data === 'string' && (data.startsWith('+') || data.startsWith('-'))) {
                  // Extract the numeric part and convert it to a number
                  return parseFloat(data);
              }
              return parseFloat(data);  // Numeric value
          }
          return data;  // Return the data for other orthogonal types
      }
      }]
    });
  
    $("#sort-select").change(function () {
      var col = $(this).val();
      console.log(col);
      // myDataTable.fnSort([ [ col, 'asc'] ]);
      myDataTable.order([col, 'asc']).draw();
      console.log(col);
    });
  
    $("#sort-order-select").change(function () {
      var direction = $(this).val();
      var col = $("#sort-select").val();
      console.log(direction);
      // myDataTable.fnSort([ [ col, 'asc'] ]);
      myDataTable.order([col, direction]).draw();
      console.log(direction);
    });
    updateDisplay();
  });

  document.addEventListener("DOMContentLoaded", function () {
    // Get references to the select elements
    const sortSelect = document.getElementById("sort-select");
    const sortOrderSelect = document.getElementById("sort-order-select");
  
    // Function to sort the cards based on the selected criteria and order
    function sortCards() {
        const cardGrid = document.querySelector(".card-grid");
        const cards = Array.from(cardGrid.querySelectorAll(".card-img"));
  
        const sortField = sortSelect.value;
        const sortOrder = sortOrderSelect.value === "asc" ? 1 : -1;
        let sortFieldName;
        console.log(sortField)
        switch (sortField) {
          case "0":
            sortFieldName = 'number';
            break;
          case "1":
            sortFieldName = 'number';
            break;
          case "2":
            sortFieldName = 'name';
            break;
          case "3":
            sortFieldName = 'aspects';
            break;
          case "4":
            sortFieldName = 'type';
            break;
          case "5":
            sortFieldName = 'arena';
            break;
          case "6":
            sortFieldName = 'cost';
            break;
          case "7":
            sortFieldName = 'power';
            break;
          case "8":
            sortFieldName = 'hp';
            break;
          case "9":
            sortFieldName = 'traits';
            break;
          case "10":
            sortFieldName = 'rarity';
            break;
          case "11":
            sortFieldName = 'artist';
            break;
          case "12":
            sortFieldName = 'penalty';
            break;
          case "13":
            sortFieldName = 'price';
            break;
        }
        const normalizeNumber = (value) => {
            if (value === undefined || value === null) return NaN;
            const cleaned = String(value).replace(/[^0-9.]/g, '');
            return cleaned ? parseFloat(cleaned) : NaN;
        };

        cards.sort((a, b) => {
            const aProperty = a.dataset[sortFieldName];
            const bProperty = b.dataset[sortFieldName];
  
            if (aProperty === "None") return -sortOrder;
            if (bProperty === "None") return sortOrder;

            if (sortFieldName === 'number') {
                const numA = normalizeNumber(aProperty);
                const numB = normalizeNumber(bProperty);
                if (!isNaN(numA) && !isNaN(numB)) {
                    if (numA < numB) return -sortOrder;
                    if (numA > numB) return sortOrder;
                    return 0;
                }
            }
  
            // Convert numeric attributes to numbers for numerical comparison
            const numA = !isNaN(aProperty) ? parseFloat(aProperty) : aProperty;
            const numB = !isNaN(bProperty) ? parseFloat(bProperty) : bProperty;
            
            if (numA < numB) return -sortOrder;
            if (numA > numB) return sortOrder;
            return 0;
        });

        // const cards = document.querySelectorAll(".card-img");
        // Append the sorted cards back to the cardGrid
        cardGrid.innerHTML = '';
        cards.forEach(card => cardGrid.appendChild(card));
    }
  
    // Event listener for changes in the select elements
    sortSelect.addEventListener("change", sortCards);
    sortOrderSelect.addEventListener("change", sortCards);

    const viewModeSelect = document.getElementById("view-mode-select");
    if (viewModeSelect) {
        viewModeSelect.addEventListener("change", function () {
            if (viewModeSelect.value === "images") {
                sortCards();
            }
        });
    }

    if (viewModeSelect && viewModeSelect.value === "images") {
        sortCards();
    }
  });


var cardRows = document.querySelectorAll('.card-row');
var offSetX = 200;
var offSetY = 220;

function hideImages() {
  var cardImages = document.querySelectorAll('.hover-card-image');
  cardImages.forEach(function (cardImage) {
    cardImage.style.display = 'none';
  });
}

function showImages(event) {
  var targetRow = event.currentTarget;
  var frontImage = targetRow.getAttribute('front-image');
  var backImage = targetRow.getAttribute('back-image');

  var frontCardImage = targetRow.querySelector('.hover-card-image.front-image');
  var backCardImage = targetRow.querySelector('.hover-card-image.back-image');

  var mouseX = event.clientX;
  var mouseY = event.clientY;

  if (frontImage) {
    frontCardImage.src = frontImage;
    frontCardImage.style.left = (mouseX + offSetX) + 'px';
    frontCardImage.style.top = (mouseY + offSetY) + 'px';
    frontCardImage.style.display = 'block';
  }

  if (backImage) {
    backCardImage.src = backImage;
    backCardImage.style.left = (mouseX + offSetX + 294) + 'px'; // Adjust the horizontal position for the back image
    backCardImage.style.top = (mouseY + offSetY + 50) + 'px'; // Adjust the vertical position for the back image
    backCardImage.style.display = 'block';
  }
}

cardRows.forEach(function (cardRow) {
  var frontCardImage = document.createElement('img');
  frontCardImage.className = 'hover-card-image front-image';
  frontCardImage.style.display = 'none';
  frontCardImage.style.position = 'fixed';
  cardRow.appendChild(frontCardImage);

  var backCardImage = document.createElement('img');
  backCardImage.className = 'hover-card-image back-image';
  backCardImage.style.display = 'none';
  backCardImage.style.position = 'fixed';
  cardRow.appendChild(backCardImage);

  cardRow.addEventListener('mouseenter', showImages);
  cardRow.addEventListener('mousemove', showImages);
  cardRow.addEventListener('mouseleave', hideImages);
});
