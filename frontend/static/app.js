let searchButton = document.querySelector(".search-button");
let clearButton = document.querySelector(".clear-button");

let fileInput = document.querySelector(".image-input");
let searchInput = document.querySelector(".query-input");

let imageContainer = document.getElementsByClassName("image-container")[0];


searchButton.addEventListener("click", function(e){
    imageContainer.style.display = "flex";
});

clearButton.addEventListener("click", function(e){
    imageContainer.style.display = "none";
});

searchInput.addEventListener('input', function(e) {
    fileInput.value = "";
})

fileInput.addEventListener('input', function(e) {
    // if (e.target.files[0]) {
    //   document.body.append('You selected ' + e.target.files[0].name);
    // }
  });