const DEBOUNCE_DELAY = 1000

// Debounce
const debounce = (func, delay) => {
  let timeout
  return executedFunction = (...args) => {
    const later = () => {
      clearTimeout(timeout)
      func(...args)
    }
    clearTimeout(timeout)
    timeout = setTimeout(later, delay)
  }
}

// Store for tracking debounced functions
const pendingUpdates = new Map()

// Update the cart on the server
const updateCartOnServer = async (productId, quantity) => {
  const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value ||
    document.querySelector('meta[name="csrf-token"]')?.getAttribute('content')
  const url = `/cart/update-product-cart/${productId}`

  try {
    const response = await fetch(url, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken,
      },
      body: JSON.stringify({ productId, quantity }),
    })

    if (!response.ok) {
      console.error(`Response status: ${response.status}`)
      throw new Error(`Network response was not ok: ${response.error}`)
    }

    return await response.json()
  } catch (error) {
    console.error('Error updating cart:', error)
  }
}

// Update cart totals in the UI
const updateCartTotals = (serverData) => {
  const cartTotalElement = document.querySelector('.cart-totals-val')
  if (serverData.total_price) {
    if (!cartTotalElement) {
      console.error('Cart total element not found in the DOM.')
    }
    cartTotalElement.textContent = `$ ${parseFloat(serverData.total_price).toFixed(2)}`
    return
  }
  // If no total price, set to $0.00 and reload the page
  if (cartTotalElement) {
    cartTotalElement.textContent = '$ 0.00'
  }
  setTimeout(() => {
    document.location.reload()
  }, 500)
}

// Update cart data both in UI
const updateCartData = async (productOrderContainer, quantity) => {
  const orderResumeSubtotal = document.querySelector('#order-resume-subtotal')
  if (!orderResumeSubtotal) {
    console.error('Order resume subtotal element not found in the DOM.')
  }

  const productOrderSubtotal = productOrderContainer.querySelector('#product-total-price')
  if (!productOrderSubtotal) {
    console.error('Order resume subtotal element not found in the DOM.')
    return
  }

  const productId = productOrderContainer.dataset.productId
  if (!productId) {
    console.error('Product ID not found in data attributes.')
    return
  }

  try {
    const serverData = await updateCartOnServer(productId.toString(), parseInt(quantity))

    if (serverData) {
      if (serverData.subtotal !== undefined) {
        // Update the product subtotal price in the UI
        if (serverData.subtotal > 0 && serverData.total_price > 0) {
          productOrderSubtotal.textContent = `$ ${serverData.subtotal}`
          orderResumeSubtotal.textContent = `$ ${serverData.total_price}`
        } else {
          // Remove product from UI if subtotal is 0

          // Remove from cart items
          const cartItemsCountElement = document.querySelector('#cart-products-count')
          if (!cartItemsCountElement) console.error('Cart total element not found in the DOM.')
          const currentCount = parseInt(cartItemsCountElement.textContent) || 0
          cartItemsCountElement.textContent = (currentCount - 1).toString()

          // Remove product from order resume UI
          productOrderContainer.remove()

          // Update order resume subtotal
          orderResumeSubtotal.textContent = `$ ${serverData.total_price}`

          // Check if cart is empty
          const remainingProducts = document.querySelectorAll('.prod-li')

          if (remainingProducts.length === 0) document.location.reload()
        }
      } else {
        console.error('Subtotal not found in server response.')
      }

      // Update cart total in the UI
      updateCartTotals(serverData)
    }

  } catch (error) {
    console.error('Error updating product total:', error)
  }
}

// Interface for debounced cart data update
const debouncedUpdateCartData = debounce((productOrderContainer, quantity) => {
  updateCartData(productOrderContainer, quantity)
}, DEBOUNCE_DELAY)

// Manage click events on quantity buttons and update quantity inputs UI
const clickQuantityButton = (buttons, operation) => {
  buttons.forEach((button) => {
    button.addEventListener('click', event => {
      event.preventDefault()

      const quantityInput = operation === 'increase'
        ? button.previousElementSibling
        : button.nextElementSibling

      if (!quantityInput) {
        console.error('Quantity input not found in the DOM.')
        return
      }

      let quantity = parseInt(quantityInput.value) || 1

      if (operation === 'increase') {
        quantity += 1
      } else if (operation === 'decrease' && quantity > 0) {
        quantity -= 1
      }

      quantityInput.value = quantity

      const productOrderContainer = button.closest('div.prod-li.sectls')

      if (!productOrderContainer) {
        console.error('Product order container not found in the DOM.')
        return
      }

      // Update Product Total UI immediately (optimistic update)
      updateLocalProductTotal(productOrderContainer, quantity)

      // Send debounced update to server
      debouncedUpdateCartData(productOrderContainer, quantity)
    })
  })
}

// Function to update local product total price in the UI
const updateLocalProductTotal = (productOrderContainer, quantity) => {
  const priceElement = productOrderContainer.querySelector('#product-price')
  const totalPriceElement = productOrderContainer.querySelector('#product-total-price')

  if (priceElement && totalPriceElement) {
    const priceText = priceElement.textContent.replace(/[$\s]/g, '')
    const price = parseFloat(priceText)

    if (!isNaN(price)) {
      const totalPrice = (price * quantity).toFixed(2)
      totalPriceElement.textContent = `$ ${totalPrice}`
    }
  }
}

// Setup listeners for quantity input changes
const setupQuantityInputListeners = () => {
  const quantityInputs = document.querySelectorAll('input[name="quantity"]')

  quantityInputs.forEach(input => {
    input.addEventListener('change', event => {
      const quantity = parseInt(event.target.value)

      if (quantity < 0) {
        event.target.value = 0
      }

      const productOrderContainer = event.target.closest('div.prod-li.sectls')
      if (!productOrderContainer) {
        console.error('Product order container not found in the DOM.')
        return
      }

      debouncedUpdateCartData(productOrderContainer, quantity)
    })
  })
}

const handleFormSubmit = () => {
  const form = document.querySelector('form.order-form')
  if (!form) {
    console.error('Order form not found in the DOM.')
    return
  }

  form.addEventListener('submit', async event => {
    event.preventDefault()
    const formData = new FormData(form)
    const submitButton = form.querySelector('button[type="submit"]')

    if (!submitButton) throw new Error('Submit button not found in the form.')

    submitButton.disabled = true
    submitButton.textContent = 'Processing...'

    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value ||
      document.querySelector('meta[name="csrf-token"]')?.getAttribute('content')

    if (!csrfToken) throw new Error('CSRF token not found in the DOM.')

    try {
      const response = await fetch(form.action, {
        method: 'POST',
        headers: {
          'X-Requested-With': 'XMLHttpRequest',
          'X-CSRFToken': csrfToken,
        },
        body: formData,
      })

      if (!response.ok) throw new Error(`Response status: ${response.status}`)

      const data = await response.json()

      if (!data.success) {
        console.error('Order submission failed:', data.error)
        alert(`Order submission failed: ${data.error || 'Unknown error'}`)
        return
      }

      if (!data.payment_url) throw new Error('Payment URL not provided in the response.')

      const paymentForm = document.createElement('form')
      paymentForm.method = 'POST'
      paymentForm.action = data.payment_url

      const csrfInput = document.createElement('input')
      csrfInput.type = 'hidden'
      csrfInput.name = 'csrfmiddlewaretoken'
      csrfInput.value = csrfToken

      paymentForm.appendChild(csrfInput)
      document.body.appendChild(paymentForm)
      paymentForm.submit()
    } catch (error) {
      console.error('Error submitting order form:', error)
    } finally {
      submitButton.disabled = false
      submitButton.textContent = 'Confirm and Pay'
    }
  })
}

document.addEventListener('DOMContentLoaded', () => {
  const quantityUpButtons = document.body.querySelectorAll('#quantity-up')
  const quantityDownButtons = document.body.querySelectorAll('#quantity-down')
  clickQuantityButton(quantityUpButtons, 'increase')
  clickQuantityButton(quantityDownButtons, 'decrease')
  setupQuantityInputListeners()
  handleFormSubmit()
})
