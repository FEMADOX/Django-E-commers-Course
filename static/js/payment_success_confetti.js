/**
 * Advanced confetti animation with multiple effects
 * Alternative to basic confetti for more celebration
 *
 * To use this version, replace the script reference in payment_completed.html:
 * <script src="{% static 'js/payment_success_confetti_advanced.js' %}" defer></script>
 */

document.addEventListener('DOMContentLoaded', () => {
  const celebrate = () => {
    const count = 200
    const defaults = {
      origin: { y: 0.7 },
      zIndex: 9999,
    }

    function fire(particleRatio, opts) {
      confetti({
        ...defaults,
        ...opts,
        particleCount: Math.floor(count * particleRatio),
      })
    }

    // Multi-stage confetti burst
    fire(0.25, {
      spread: 26,
      startVelocity: 55,
    })

    fire(0.2, {
      spread: 60,
    })

    fire(0.35, {
      spread: 100,
      decay: 0.91,
      scalar: 0.8,
    })

    fire(0.1, {
      spread: 120,
      startVelocity: 25,
      decay: 0.92,
      scalar: 1.2,
    })

    fire(0.1, {
      spread: 120,
      startVelocity: 45,
    })

    // Continuous confetti for 3 seconds
    const duration = 2500
    const animationEnd = Date.now() + duration

    const interval = setInterval(() => {
      const timeLeft = animationEnd - Date.now()

      if (timeLeft <= 0) {
        return clearInterval(interval)
      }

      confetti({
        particleCount: 2,
        angle: 60,
        spread: 55,
        origin: { x: 0 },
        colors: ['#22c55e', '#1291ee', '#fbbf24'],
        zIndex: 9999,
      })

      confetti({
        particleCount: 2,
        angle: 120,
        spread: 55,
        origin: { x: 1 },
        colors: ['#22c55e', '#1291ee', '#fbbf24'],
        zIndex: 9999,
      })
    }, 50)
  }

  // Start celebration after page loads
  celebrate()
})
