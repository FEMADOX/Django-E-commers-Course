const closeButtons = document.getElementsByClassName("close")

// Close message by clicking the "x" button
Array.from(closeButtons).forEach((btn) => {
    btn.addEventListener("click", function (event) {
        event.preventDefault();
        this.parentElement.style.display = "none";
    });
});
