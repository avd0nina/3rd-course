describe('Покупки', () => {
  it('Делаем покупку первого предмета в списке', () => {

    // Шаг 1: Открываем сайт
    cy.visit('https://www.saucedemo.com/')

    // Шаг 2: Авторизация
    cy.get('[data-test="username"]').type('standard_user', { delay: 200 })
    cy.get('[data-test="password"]').type('secret_sauce', { delay: 200 })
    cy.get('[data-test="login-button"]').click()
    cy.wait(1000)

    // Шаг 3: Проверяем, что мы в каталоге товаров
    cy.url().should('include', '/inventory')

    // Шаг 4: Добавляем первый товар в корзину
    cy.get('[data-test="add-to-cart-sauce-labs-backpack"]').click()
    cy.wait(1000)

    // Проверяем значок корзины
    cy.get('[data-test="shopping-cart-badge"]').invoke('text').should('equal', '1')

    // Шаг 5: Переходим в корзину
    cy.get('[data-test="shopping-cart-link"]').click()
    cy.wait(1000)

    // Проверяем название и цену товара в корзине
    cy.get('[data-test="inventory-item-name"]').invoke('text').should('equal', 'Sauce Labs Backpack')
    cy.get('[data-test="inventory-item-price"]').invoke('text').should('equal', '$29.99')

    // Шаг 6: Переходим в чекаут
    cy.get('[data-test="checkout"]').click()
    cy.wait(1000)

    // Заполняем данные доставки
    cy.get('[data-test="firstName"]').type('TEST', { delay: 200 })
    cy.get('[data-test="lastName"]').type('USER', { delay: 200 })
    cy.get('[data-test="postalCode"]').type('12345567', { delay: 200 })
    cy.get('[data-test="continue"]').click()
    cy.wait(1000)

    // Шаг 7: Завершаем покупку
    cy.get('[data-test="finish"]').click()
    cy.wait(1000)

    // Финальная проверка
    cy.get('[data-test="complete-header"]').invoke('text').should('equal', 'Thank you for your order!')
  })
})