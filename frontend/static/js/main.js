document.addEventListener("DOMContentLoaded", function () {

    const button = document.getElementById("testButton");

    if (button) {
        button.addEventListener("click", function () {
            alert("Frontend JavaScript is working!");
        });
    }

});