document.addEventListener("DOMContentLoaded", () => {
    let counter = 60
    const resendButton = document.getElementById('resend-button')
    const form = document.querySelector('form.email-validation')
    let isSubmitting = false

    form.onsubmit = event => {
        if (counter > 0) {
            event.preventDefault()
            return false
        }

        if (!isSubmitting) {
            isSubmitting = true
            resendButton.value = 'Submitting...'
            resendButton.disabled = true
            return true
        }
    }

    resendButton.value = `Resend Email in (${counter})s`
    resendButton.disabled = counter > 0

    const timer = setInterval(() => {
        counter--
        resendButton.value = `Resend Email in (${counter})s`
        resendButton.disabled = counter > 0
        if (counter <= 0) {
            resendButton.value = 'Resend Email'
            clearInterval(timer)
        }
    }, 1000)
})
