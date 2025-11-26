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
    const url = `update-product-cart/${productId}`

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
            const responseJson = await response.json()
            throw new Error(`Network response was not ok: ${responseJson.error}`)
        }

        return await response.json()
    } catch (error) {
        console.error('Error updating cart:\n', error)
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
    const cartTotalElement = document.querySelector('.cart-totals-val')
    if (!cartTotalElement) {
        console.error('Cart total element not found in the DOM.')
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
                    cartTotalElement.textContent = `$ ${serverData.total_price}`
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
                    cartTotalElement.textContent = `$ ${serverData.total_price}`

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

            const productCartContainer = button.closest('article.prod-li.sectls')

            if (!productCartContainer) {
                console.error('Product cart container not found in the DOM.')
                return
            }

            // Send debounced update to server
            debouncedUpdateCartData(productCartContainer, quantity)
        })
    })
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

            const productOrderContainer = event.target.closest('article.prod-li.sectls')
            if (!productOrderContainer) {
                console.error('Product order container not found in the DOM.')
                return
            }

            debouncedUpdateCartData(productOrderContainer, quantity)
        })
    })
}

document.addEventListener('DOMContentLoaded', () => {
    const quantityUpButtons = document.body.querySelectorAll('#quantity-up')
    const quantityDownButtons = document.body.querySelectorAll('#quantity-down')
    clickQuantityButton(quantityUpButtons, "increase")
    clickQuantityButton(quantityDownButtons, "decrease")
    setupQuantityInputListeners()
})
