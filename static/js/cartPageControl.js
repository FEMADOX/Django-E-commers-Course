const updateCartOnServer = async (productId, quantity) => {
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value ||
        document.querySelector('meta[name="csrf-token"]')?.getAttribute('content')
    const actualUrl = window.location.href

    try {
        const response = await fetch(`${actualUrl}update-product-cart/${productId}`, {
            // method: 'PUT',
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken,
            },
            body: JSON.stringify({quantity}),
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

const updateCartTotals = (serverData) => {
    const cartTotalElement = document.querySelector('.cart-totals-val')
    if (serverData.total_price) {
        if (!cartTotalElement) {
            console.error('Cart total element not found in the DOM.')
        }
        cartTotalElement.textContent = `$${parseFloat(serverData.total_price).toFixed(2)}`
        return
    }
    // If no total price, set to $0.00 and reload the page
    cartTotalElement.textContent = '$0.00'
    document.location.reload()
}

// TODO: Implement product removal when quantity is 0
const updateCartData = async (button, quantity) => {
    const productContainer = button.closest('.prod-li-cont')
    const totalPriceElement = productContainer.querySelector('#product-total-price')
    const productId = totalPriceElement.dataset.productId

    if (!productId) {
        console.error('Product ID not found in data attributes.')
        return
    }

    try {
        const serverData = await updateCartOnServer(productId, quantity)

        if (serverData) {
            if (serverData.subtotal) {
                // Update the product subtotal price in the UI
                if (serverData.subtotal > 0) {
                    totalPriceElement.textContent = `$${parseFloat(serverData.subtotal).toFixed(2)}`
                } else {
                    // Remove product from UI if subtotal is 0
                    const productArticle = button.closest('article.prod-li.sectls')
                    const cartItemsCountElement = document.querySelector('#cart-products-count')
                    if (!productArticle) {
                        console.error('Product article not found in the DOM.')
                    }
                    // Reduce cart items count
                    cartItemsCountElement.textContent = (parseInt(cartItemsCountElement.textContent) - 1).toString()
                    productArticle.remove()
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

const clickQuantityButton = (buttons, operation) => {
    buttons.forEach((button, index) => {
        button.addEventListener('click', event => {
            event.preventDefault()
            let quantityInput = button
            let quantity = 0

            if (operation === 'increase') {
                quantityInput = button.nextElementSibling
                quantity = parseInt(quantityInput.value)
                quantity += 1
            } else if (operation === 'decrease') {
                quantityInput = button.previousElementSibling
                quantity = parseInt(quantityInput.value)

                if (quantity >= 1) {
                    quantity -= 1
                }
            }

            quantityInput.value = quantity

            // Update the product total price UI
            updateCartData(button, quantity)
        })
    })
}

const setupQuantityInputListeners = () => {
    const quantityInputs = document.querySelectorAll('input[name="quantity"]')

    quantityInputs.forEach(input => {
        input.addEventListener('change', event => {
            const quantity = parseInt(event.target.value)

            if (quantity < 1) {
                event.target.value = 1
                return
            }

            updateCartData(event.target, quantity)
        })

        input.addEventListener('input', event => {
            const quantity = parseInt(event.target.value) || 1
            const button = event.target
            const productContainer = button.closest('.prod-li-cont')
            const priceElement = productContainer.querySelector('#product-price')
            const totalPriceElement = productContainer.querySelector('#product-total-price')

            const price = parseFloat(priceElement.textContent.replace('$', ''))
            const totalPrice = (price * quantity).toFixed(2)

            totalPriceElement.textContent = `$${totalPrice}`
        })
    })
}

const quantityUpButtons = document.querySelectorAll('#quantity-up')
const quantityDownButtons = document.querySelectorAll('#quantity-down')
clickQuantityButton(quantityUpButtons, "increase")
clickQuantityButton(quantityDownButtons, "decrease")
setupQuantityInputListeners()
