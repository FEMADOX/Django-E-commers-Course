// Obtaining the darkmode status
var darkmode = localStorage.getItem("darkmode")
// Obtaining the theme switch button
const themeSwitch = document.getElementById("theme-switch")

// Functions to enable darkmode
const enableDarkmode = () => {
    document.body.classList.add("darkmode")
    localStorage.setItem("darkmode", "active")
}

// Functions to disable darkmode
const disableDarkmode = () => {
    document.body.classList.remove("darkmode")
    localStorage.setItem("darkmode", null)
}

// Checking the darkmode status and applying the corresponding theme
if (darkmode === "active") {
    enableDarkmode();
} else if (darkmode === "inactive") {
    disableDarkmode();
} else {
    // If there is no preference stored, use the system's configuration
    if (window.matchMedia && window.matchMedia("(color-scheme: dark)").matches) {
        enableDarkmode();
    } else {
        disableDarkmode();
    }
}

// Switching between modes when the user clicks the button
themeSwitch.addEventListener("click", () => {
    darkmode = localStorage.getItem("darkmode")
    darkmode !== "active" ? enableDarkmode() : disableDarkmode()
})