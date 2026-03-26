describe('Отображение товара в листинге и карточке для стандартного пользователя', () => {
  it('Проверки названия и цены рюкзака', () => {

    // Открываем сайт
    cy.visit('https://www.saucedemo.com/')

    // Авторизуемся стандартным пользователем
    cy.get('[data-test="username"]').type('standard_user', { delay: 200 })
    cy.get('[data-test="password"]').type('secret_sauce', { delay: 200 })
    cy.get('[data-test="login-button"]').click()
    cy.wait(1000)

    // Проверяем, что мы попали в список товаров
    cy.url().should('include', '/inventory')

    // Проверяем название и цену ПЕРВОГО товара в списке
    cy.get('[data-test="inventory-item-name"]').eq(0).invoke('text').should('equal', 'Sauce Labs Backpack')
    cy.get('[data-test="inventory-item-price"]').eq(0).invoke('text').should('equal', '$29.99')

    // Переходим в карточку первого товара (кликаем по названию)
    cy.get('[data-test="inventory-item-name"]').eq(0).click()
    cy.wait(1000)

    // Проверяем, что URL изменился на карточку товара
    cy.url().should('include', '/inventory-item')

    // Проверяем название и цену уже внутри карточки товара
    cy.get('[data-test="inventory-item-name"]').invoke('text').should('equal', 'Sauce Labs Backpack')
    cy.get('[data-test="inventory-item-price"]').invoke('text').should('equal', '$29.99')
  })
})