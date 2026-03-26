describe('Добавление товара в корзину и удаление для стандартного пользователя', () => {
  it('Добавляем Sauce Labs Bolt T-Shirt в корзину и удаляем из корзины', () => {
    
    // Открываем сайт
    cy.visit('https://www.saucedemo.com/')
    
    // Авторизуемся
    cy.get('[data-test="username"]').type('standard_user', {delay: 200})
    cy.get('[data-test="password"]').type('secret_sauce', {delay: 200})
    cy.get('[data-test="login-button"]').click()
    cy.wait(1000)
   
    // Проверяем, что url изменился
    
    cy.url().should('include', '/inventory')
    
    // Проверяем, что Sauce Labs Bolt T-Shirt видим на странице
    cy.get('[data-test="add-to-cart-sauce-labs-bolt-t-shirt"]').should('be.visible')
    
    // Добавляем Sauce Labs Bolt T-Shirt в корзину
    cy.get('[data-test="add-to-cart-sauce-labs-bolt-t-shirt"]').click()
    cy.wait(1000)
    
    // Проверяем, что значок на корзине = 1
    cy.get('[data-test="shopping-cart-badge"]').invoke('text').should('equal', '1')
    cy.wait(1000)
    
    // Удаляем добавленный товар
    cy.get('[data-test="remove-sauce-labs-bolt-t-shirt"]').click()
    cy.wait(1000)
    
    // Проверяем, что значок на корзине отсутствует
    cy.get('[data-test="shopping-cart-badge"]').should('not.exist')
  })
})

