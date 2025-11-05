document.addEventListener('DOMContentLoaded', () => {
  const togglePasswordIcons = document.querySelectorAll('.password-toggle-icon')

  if (togglePasswordIcons.length === 0) {
    console.error('No password toggle icons found')
    return
  }

  togglePasswordIcons.forEach(icon => {
    icon.addEventListener('click', event => {
      const clickedIcon = event.currentTarget
      const wrapper = clickedIcon.closest('.password-wrapper')

      if (!wrapper) {
        console.error('Password wrapper not found')
        return
      }

      const passwordInput = wrapper.querySelector('input[type="password"], input[type="text"]')

      if (!passwordInput) {
        console.error('Password input not found in wrapper')
        return
      }

      // Toggle Input type
      const newType = passwordInput.type === 'password' ? 'text' : 'password'
      passwordInput.type = newType

      // Toggle icon
      clickedIcon.classList.toggle('bi-eye')
      clickedIcon.classList.toggle('bi-eye-slash')
    })
  })
})
