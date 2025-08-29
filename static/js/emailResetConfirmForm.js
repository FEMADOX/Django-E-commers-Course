const spanHelpText1 = document.querySelector("#id_new_password1_helptext")
const spanHelpText2 = document.querySelector("#id_new_password2_helptext")
const ulErrorList = document.querySelector("#id_new_password2_error")

if (ulErrorList && ulErrorList.classList.contains("errorlist")) {
    spanHelpText1.innerText = ""
    spanHelpText2.innerText = ""
}
