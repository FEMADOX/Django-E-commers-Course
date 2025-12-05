document.addEventListener('DOMContentLoaded', () => {
  const shareBtn = document.getElementById('btn-share')
  if (!shareBtn) return

  shareBtn.addEventListener('click', async () => {
    const url = shareBtn.dataset.url
    const title = shareBtn.dataset.title

    // Check if Web Share API is supported
    if (navigator.share) {
      try {
        await navigator.share({
          title: title,
          text: `Check out this product: ${title}`,
          url: url,
        })
      } catch (err) {
        if (err.name !== 'AbortError') {
          console.error('Error sharing:', err)
        }
      }
    } else {
      // Fallback: Copy to clipboard
      try {
        window.focus()

        await navigator.clipboard.writeText(url)

        // Show feedback
        const originalIcon = shareBtn.innerHTML
        shareBtn.innerHTML = '<i class="bi bi-check"></i>'
        shareBtn.classList.add('success')

        const toast = document.createElement('div')
        toast.className = 'toast-container'
        toast.innerHTML = `
          <div class="toast align-items-center border-0 success fade show" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="toast-content d-flex">
              <div class="toast-body">Link copied to clipboard!</div>
              <button
                type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"
                onClick="closeToast(this)"
              ></button>
            </div>
          </div>
        `
        document.body.appendChild(toast)

        // Initialize the new toast
        const toastElement = toast.querySelector('.toast')
        const bsToast = new bootstrap.Toast(toastElement, { autohide: false })
        bsToast.show()

        setTimeout(() => {
          if (!toastElement.checkVisibility()) return

          toastElement.classList.add('closed')
          toastElement.addEventListener('animationend', handleAnimationEnd)
        }, 5000)

        // Change Share button back after 2 seconds
        setTimeout(() => {
          shareBtn.innerHTML = originalIcon
          shareBtn.classList.remove('success')
        }, 2000)
      } catch (err) {
        console.error('Failed to copy:', err)
        alert('Failed to copy link')
      }
    }
  })
})
