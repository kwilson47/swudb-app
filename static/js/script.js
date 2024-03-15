document.addEventListener('DOMContentLoaded', function () {
  // const cardImages = document.querySelectorAll('.card-image');
  var toggleableCards = document.querySelectorAll('.toggleable');
  toggleableCards.forEach(function (cardImage) {
    cardImage.addEventListener('click', function () {
      const backImage = cardImage.getAttribute('data-back-image');
      const currentSrc = cardImage.getAttribute('src');

      if (currentSrc === backImage) {
        // Display front side
        cardImage.setAttribute('src', cardImage.getAttribute('data-front-image'));
      } else {
        // Display back side
        cardImage.setAttribute('src', backImage);
      }
    });
  });
});

$(document).ready(function(){
  $('[data-bs-toggle="tooltip"]').tooltip();
});



function buildUpdatedURL(sortField, sortOrder, selectedDisplayMode) {
  const currentURL = window.location.href;
  let updatedURL;

  // Check if the URL already contains the 'sort' parameter
  if (currentURL.includes('&sort=')) {
    updatedURL = currentURL.replace(/(&|\?)sort=[^&]+/, '$1sort=' + sortField);
  } else {
    // Append the 'sort' parameter to the URL
    updatedURL = currentURL + (currentURL.includes('?') ? '&' : '?') + 'sort=' + sortField;
  }

  // Check if the URL already contains the 'sort' parameter
  if (updatedURL.includes('&sortOrder=')) {
    updatedURL = updatedURL.replace(/(&|\?)sortOrder=[^&]+/, '$1sortOrder=' + sortOrder);
  } else {
    // Append the 'sort' parameter to the URL
    updatedURL = updatedURL + (updatedURL.includes('?') ? '&' : '?') + 'sortOrder=' + sortOrder;
  }


  return updatedURL;
}

// Attach event listener to all toggle buttons
const toggleButtons = document.querySelectorAll('.toggle-button');
toggleButtons.forEach(button => {
  button.addEventListener('click', () => {
    // Find the image element within the button's parent container
    const image = button.parentNode.querySelector('.card-image');
    // Toggle the image by changing its source or visibility
    // Implement your specific logic here
    const backImage = image.getAttribute('data-back-image');
    const currentSrc = image.getAttribute('src');

    if (currentSrc === backImage) {
      // Display front side
      image.setAttribute('src', image.getAttribute('data-front-image'));
    } else {
      // Display back side
      image.setAttribute('src', backImage);
    }
  });
});

// Get the modal
var modal = document.getElementById("myModal");

// Get the <span> element that closes the modal
var span = document.getElementsByClassName("close-modal")[0];

// When the user clicks on <span> (x), close the modal
span.onclick = function() {
  modal.style.display = "none";
}

// When the user clicks anywhere outside of the modal, close it
window.onclick = function(event) {
  if (event.target == modal) {
    modal.style.display = "none";
  }
}

// Get all buttons that open modals
var buttons = document.getElementsByClassName("myBtn");

// Function to handle button click event
for (var i = 0; i < buttons.length; i++) {
  buttons[i].onclick = function() {
      modal.style.display = "block";
      var tcgProductId = this.getAttribute('data-tcg-product-id');
      var cardSetName = this.getAttribute('data-card-set');
      var cardName = this.getAttribute('data-card-name');
      var cardNumber = this.getAttribute('data-card-number');


      // Make AJAX request to Flask backend
      $.ajax({
          type: 'GET',
          url: '/get_prices',
          data: {
              tcg_product_id: tcgProductId
          },
          success: function (response) {
              // Populate modal with data received from backend
              populateModal(response, cardSetName, cardNumber, cardName);
          },
          error: function (xhr, status, error) {
              console.error('Error:', error);
          }
      });
  };
}

// Function to populate modal with data
function populateModal(data, cardSetName, cardNumber, cardName) {
  // Clear previous data
  $('#card-price-details-modal-entries').empty();

  // Iterate through each entry in data and populate modal
  data.forEach(function (entry) {
      var modalEntry = $('<div class="card-price-details-modal-entry"></div>');
      var variantTypeName = $('<div class="card-price-details-modal-entry-card-variant-type-name-container">' + entry.subTypeName + '</div>');
      var pricesContainer = $('<div class="card-price-details-modal-entry-prices"></div>');

      // Populate prices
      var priceLabels = ['market', 'low', 'mid', 'high'];
      priceLabels.forEach(function (label) {
          var priceEntry = $('<div class="card-price-details-modal-entry-price"></div>');
          priceEntry.append('<span class="card-price-details-modal-entry-price-label">' + label + '</span>');
          
          console.log(entry[label]);
          // Format price with 2 decimal places
          if (entry[label] === '' || isNaN(entry[label])) {
            formattedPrice = 'None';
          } else {
              // Format price with 2 decimal places
              formattedPrice = '$' + parseFloat(entry[label]).toFixed(2);
          }
          console.log(formattedPrice);
          priceEntry.append('<span class="card-price-details-modal-entry-price-value">' + formattedPrice + '</span>');
          pricesContainer.append(priceEntry);
      });

      modalEntry.append(variantTypeName);
      modalEntry.append(pricesContainer);

      // Append the link
      var link = $('<a href="' + entry['url'] +'" rel="external nofollow" target="_blank" class="card-price-details-modal-entry-vendor-button button button-plain button-small"></a>');
      link.append('<span aria-hidden="true" class="button-icon fa-solid fa-up-right-from-square"></span>');
      link.append('View on TCGplayer');
      modalEntry.append(link);

      $('#card-price-details-modal-entries').append(modalEntry);
  });

  // Populate modal title
  var modalTitle = 'Prices of <em>' + cardName + ' (' + cardSetName + ' ' + cardNumber + ')</em>';
  $('.my-modal-title').html(modalTitle);
}

// Function to initialize the button event listeners and append buttons to each card
function initializeButtons() {
  const buttons = document.querySelectorAll(".card-image-controls-item-price");
  buttons.forEach(button => {
      button.addEventListener("click", function() {
          const cardSet = button.dataset.cardSet;
          const cardNumber = button.dataset.cardNumber;
          const cardName = button.dataset.cardName;
          const tcgProductId = button.dataset.tcgProductId;
          // Call function to open modal with appropriate data
          openModal(cardSet, cardNumber, cardName, tcgProductId);
      });
  });
}

// Call initializeButtons function once during initialization
initializeButtons();