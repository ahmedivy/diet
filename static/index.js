const allergiesCheckbox = document.getElementById("allergies-checkbox");
const allergiesInput = document.getElementById("allergies-input");
const submitButton = document.getElementById("submit-button");

allergiesInput.style.display = "none";

allergiesCheckbox.addEventListener("change", (event) => {
  if (event.target.checked) {
    console.log("Allergies checkbox is checked!");
    allergiesInput.style.display = "block";
  } else {
    console.log("Allergies checkbox is unchecked!");
    allergiesInput.style.display = "none";
  }
});

submitButton.addEventListener("click", (event) => {
  event.preventDefault(); // prevent form submission

  const nameInput = document.getElementById("name");
  const ageInput = document.getElementById("age");
  const genderInput = document.getElementById("gender");
  const weightInput = document.getElementById("weight");
  const heightInput = document.getElementById("height");
  const daysInput = document.getElementById("days");
  const dietInput = document.querySelector('input[name="diet"]:checked');
  const allergiesCheckbox = document.getElementById("allergies-checkbox");
  const allergiesInput = document.getElementById("allergies");

  // validate inputs
  if (
    nameInput.value.trim() === "" ||
    ageInput.value === "" ||
    genderInput.value === "" ||
    weightInput.value === "" ||
    heightInput.value === "" ||
    daysInput.value === "" ||
    dietInput === null ||
    (allergiesCheckbox.checked && allergiesInput.value.trim() === "")
  ) {
    alert("Please fill in all required fields.");
    return;
  }

  // create object
  const userObject = {
    name: nameInput.value.trim(),
    age: parseInt(ageInput.value),
    gender: genderInput.value,
    weight: parseFloat(weightInput.value),
    height: parseFloat(heightInput.value),
    days: parseInt(daysInput.value),
    diet: dietInput.value,
    allergies: allergiesCheckbox.checked
      ? allergiesInput.value.trim().split(",")
      : [],
  };

  // print object to console
  console.log(userObject);

  // send POST request to Flask backend
  fetch("/api/info", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(userObject),
  }).then((response) => {
    if (response.redirected) {
      window.location.href = response.url;
    } else {
      throw new Error("POST request failed.");
    }
  });
});
