document.addEventListener('DOMContentLoaded', () => {
  const section = document.querySelector('#catalog-section')

  if (!section) {
    console.error('Catalog section not found')
    return
  }

  const articles = section.querySelectorAll('article')
  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        if (!entry.target.classList.contains('show-on-scroll')) {
          entry.target.classList.add('show-on-scroll')
        }
      }
      else {
        entry.target.classList.remove('show-on-scroll')
      }
    })
  },
    {
      threshold: 0,
      rootMargin: '-30px 0px -50px 0px'
    })

  articles.forEach(article => observer.observe(article))
})
