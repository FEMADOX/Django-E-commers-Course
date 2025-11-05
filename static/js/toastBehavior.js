const handleAnimationEnd = event => {
    console.log('Animation ended:', event)
    const toastElement = event.target
    const animationName = event.animationName
    if (toastElement.classList.contains('closed') && animationName === 'dismissToast') {
        toastElement.remove()
    }
}

// Toast behavior for Django messages
document.addEventListener('DOMContentLoaded', () => {
  // const toastElList = [].slice.call(document.querySelectorAll('.toast'))
  const toastElList = document.querySelectorAll('.toast')

  toastElList.forEach(toastElement => {
    const toast = new bootstrap.Toast(toastElement, { autohide: false })
    toast.show()

    // Auto-hide after 5 seconds
    setTimeout(() => {
      if (!toastElement.checkVisibility()) return

      toastElement.classList.add('closed')
      toastElement.addEventListener('animationend', handleAnimationEnd)
    }, 5000)

    return toast
  })
})

// Handle manual close button clicks
const closeToast = button => {
  const toastElement = button.closest('.toast')
  toastElement.classList.add('closed')
  toastElement.addEventListener('animationend', handleAnimationEnd)
}
