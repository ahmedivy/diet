var input = document.getElementById("products-input");
var table = document.getElementById("products-table");
var cart = document.getElementById("cart-table");
let searchButton = document.getElementById("search-button");
let resetButton = document.getElementById("reset-button");
let clearCart = document.getElementById("clear-btn");

clearCart.addEventListener("click", () => {
  var rowCount = cart.rows.length;
  for (var i = rowCount - 1; i > 0; i--) {
    cart.deleteRow(i);
  }
  updateNutrients();
});

let originalProducts = [];

let currentCount = 0;
let loadMoreButton = document.getElementById("loadmoreButton");

loadMoreButton.addEventListener("click", loadMore);

async function loadMore() {
  if (currentCount >= originalProducts.length) {
    return;
  }
  updateTable(originalProducts.slice(currentCount, currentCount + 400), true);
  currentCount += 400;
}

function updateTable(filteredProducts, isLoadMore = false) {
  // Clear previous table rows
  if (!isLoadMore) {
    table.innerHTML = "";
  }

  // Create table rows for each product
  filteredProducts.forEach(function (product) {
    var row = table.insertRow();
    var nameCell = row.insertCell();
    nameCell.textContent = product.name;

    // Add a button column with "Add to Cart" button
    var buttonCell = row.insertCell();
    var addButton = document.createElement("button");
    addButton.classList.add("btn", "btn-primary");
    addButton.innerHTML = '<i class="bi bi-cart-fill"></i> Add';

    // Add event handler to the button (to be implemented later)
    addButton.addEventListener("click", function () {
      var array = Array.from(cart.rows);
      array.shift();
      var existingRow = array.find((r) => {
        console.log(r);
        console.log(product);
        return parseInt(r.cells[0].textContent) === product.code;
      });
      if (existingRow) {
        quantityCell = existingRow.cells[2];
        quantityCell.textContent = parseInt(quantityCell.textContent) + 1;
        updateNutrients();
        return;
      }

      // Handle the "Add to Cart" button click
      console.log("Add to Cart clicked for", product.name);
      var row = cart.insertRow();
      var codeCell = row.insertCell();
      codeCell.style.display = "none";
      codeCell.textContent = product.code;
      var nameCell = row.insertCell();
      nameCell.textContent = product.name;
      var quantityCell = row.insertCell();
      quantityCell.textContent = 1;
      var buttonCell = row.insertCell();
      var buttonGroup = document.createElement("div");
      buttonGroup.classList.add("btn-group");
      var addButton = document.createElement("button");
      addButton.classList.add("btn", "btn-success");
      addButton.innerHTML = '<i class="bi bi-plus-lg"></i>';
      addButton.addEventListener("click", function () {
        // Handle the "+" button click
        quantityCell.textContent = parseInt(quantityCell.textContent) + 1;
        // Also add code of product to cart hiddenly
        updateNutrients();
      });
      var removeButton = document.createElement("button");
      removeButton.classList.add("btn", "btn-danger");
      removeButton.innerHTML = '<i class="bi bi-dash-lg"></i>';
      removeButton.addEventListener("click", function () {
        // Handle the "-" button click
        var quantity = parseInt(quantityCell.textContent) - 1;
        if (quantity === 0) {
          row.remove();
        } else {
          quantityCell.textContent = quantity;
        }
        updateNutrients();
      });
      buttonGroup.appendChild(addButton);
      buttonGroup.appendChild(removeButton);
      buttonCell.appendChild(buttonGroup);
      updateNutrients();
    });
    buttonCell.appendChild(addButton);
  });
}

fetch("/api/products", { method: "GET" })
  .then((response) => response.json())
  .then((data) => {
    products = data.products;

    originalProducts = [...products];

    updateTable(products.slice(0, 400), true);
    currentCount = 400;

    input.addEventListener("keyup", (event) => {
      if (event.key === "Enter") {
        var inputValue = input.value.toLowerCase();

        var filteredProducts = originalProducts.filter(function (product) {
          return product.name.toLowerCase().startsWith(inputValue);
        });

        updateTable(filteredProducts);
      }
    });

    searchButton.addEventListener("click", function () {
      var inputValue = input.value.toLowerCase();

      var filteredProducts = originalProducts.filter(function (product) {
        return product.name.toLowerCase().includes(inputValue);
      });

      updateTable(filteredProducts);
    });

    resetButton.addEventListener("click", function () {
      input.value = "";

      currentCount = 400;
      updateTable(originalProducts.slice(0, 400));
    });
  });

let suggestionsTable = document.getElementById("suggestions-table");
let refreshButton = document.getElementById("refreshSuggestions");
let suggestionDescription = document.getElementById("suggestionsDescription");
let tableBody = document.getElementById("suggestions-table-body");
let cartBody = document.getElementById("cart-body");

suggestionDescription.textContent = "";
refreshButton.addEventListener("click", updateSuggestions);

function getCart() {
  var rows = Array.from(cart.rows);
  rows.shift();
  var items = {};
  rows.forEach((row) => {
    items[row.cells[0].textContent] = parseInt(row.cells[2].textContent);
  });
  return items;
}

async function updateSuggestions() {
  var items = getCart();

  try {
    const response = await fetch("/api/suggestions", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ items: items }),
    });
    const data = await response.json();
    console.log(data);
    var description = data.desc;
    var products = data.items;
    if (description == "No suggestions") {
      suggestionDescription.textContent =
        "All nutrients are satisfied! No more suggestions! 😉";
      tableBody.innerHTML = "";
    } else {
      suggestionDescription.textContent = "";
      tableBody.innerHTML = "";
      products.forEach(function (item) {
        var row = tableBody.insertRow();
        var codeCell = row.insertCell();
        var nameCell = row.insertCell();
        var quantityCell = row.insertCell();
        var buttonCell = row.insertCell();
        codeCell.style.display = "none";
        codeCell.innerHTML = item.code;
        nameCell.innerHTML = item.name;
        quantityCell.innerHTML = item.quantity;
        var button = document.createElement("button");
        if (description == "Add products") {
          button.classList.add("btn", "btn-success");
          button.innerHTML = '<i class="bi bi-plus-lg"></i>';
          button.addEventListener("click", addProduct);
          buttonCell.appendChild(button);
          suggestionDescription.textContent = "";
        } else {
          button.classList.add("btn", "btn-danger");
          button.innerHTML = '<i class="bi bi-dash-lg"></i>';
          button.addEventListener("click", removeProduct);
          suggestionDescription.textContent = "";
          buttonCell.appendChild(button);
        }
      });
    }
  } catch (error) {
    console.error(error);
  }
}

function addProduct() {
  var row = this.parentNode.parentNode;
  var code = row.cells[0].textContent;
  var name = row.cells[1].textContent;
  var quantity = parseInt(row.cells[2].textContent);
  var cartRows = Array.from(cart.rows);
  cartRows.shift();
  var cartRow = cartRows.find((r) => r.cells[0].textContent == code);
  if (cartRow) {
    cartRow.cells[2].textContent =
      parseInt(cartRow.cells[2].textContent) + quantity;
  } else {
    var cartRow = cartBody.insertRow();
    var codeCell = cartRow.insertCell();
    var nameCell = cartRow.insertCell();
    var quantityCell = cartRow.insertCell();
    var buttonCell = cartRow.insertCell();
    codeCell.innerHTML = code;
    codeCell.style.display = "none";
    nameCell.innerHTML = name;
    quantityCell.innerHTML = quantity;
    var buttonGroup = document.createElement("div");
    buttonGroup.classList.add("btn-group");
    buttonGroup.setAttribute("role", "group");
    var addButton = document.createElement("button");
    addButton.classList.add("btn", "btn-success");
    addButton.innerHTML = '<i class="bi bi-plus-lg"></i>';
    addButton.addEventListener("click", function () {
      quantityCell.textContent = parseInt(quantityCell.textContent) + 1;
      updateNutrients();
    });
    var removeButton = document.createElement("button");
    removeButton.classList.add("btn", "btn-danger");
    removeButton.innerHTML = '<i class="bi bi-dash-lg"></i>';
    removeButton.addEventListener("click", function () {
      var quantity = parseInt(quantityCell.textContent) - 1;
      if (quantity === 0) {
        cartRow.remove();
      } else {
        quantityCell.textContent = quantity;
      }
      updateNutrients();
    });
    buttonGroup.appendChild(addButton);
    buttonGroup.appendChild(removeButton);
    buttonCell.appendChild(buttonGroup);
  }
  row.remove();
  updateNutrients();
}

function removeProduct() {
  var row = this.parentNode.parentNode;
  var code = row.cells[0].textContent;
  var name = row.cells[1].textContent;
  var quantity = parseInt(row.cells[2].textContent);
  var cartRows = Array.from(cart.rows);
  cartRows.shift();
  var cartRow = cartRows.find((row) => row.cells[0].textContent == code);
  if (cartRow) {
    cartRow.cells[2].textContent =
      parseInt(cartRow.cells[2].textContent) - quantity;
    if (parseInt(cartRow.cells[2].textContent) === 0) {
      cartRow.remove();
    }
  }
  row.remove();
  updateNutrients();
}

async function updateNutrients() {
  console.log("Updating nutrients");
  var items = getCart();
  console.log(items);
  try {
    const response = await fetch("/api/nutrients", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ items: items }),
    });
    console.log(JSON.stringify({ items: items }));
    const data = await response.json();
    console.log("Success:", data);
    var nutrients = data.nutrients;
    for (var key in nutrients) {
      document.getElementById("cart-" + key.toLowerCase()).textContent =
        nutrients[key];
    }
  } catch (error) {
    console.error("Error:", error);
  }
}
