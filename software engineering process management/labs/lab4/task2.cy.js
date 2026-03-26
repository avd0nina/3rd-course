describe('Отображение товара в листинге и карточке для проблемного пользователя', () => {
  it('Делаем покупку первого предмета в списке', () => {
    
    // Открываем сайт
    cy.visit('https://www.saucedemo.com/')
    
    // Авторизуемся
    cy.get('[data-test="username"]').type('problem_user', {delay: 200})
    cy.get('[data-test="password"]').type('secret_sauce', {delay: 200})
    cy.get('[data-test="login-button"]').click()
    cy.wait(1000)
    
    // Проверяем, что url изменился
    cy.url().should('include', '/inventory')
    
    // Проверяем, что наименование первого предмета 'Sauce Labs Backpack' и цена '$29.99' 
    cy.get('[data-test="inventory-item-name"]').eq(0).invoke('text').should('equal', 'Sauce Labs Backpack')
    cy.get('[data-test="inventory-item-price"]').eq(0).invoke('text').should('equal', '$29.99')
    
    //Кликаем по первому предмету
    cy.get('[data-test="inventory-item-name"]').eq(0).click()
    
    // Проверяем, что url изменился
    cy.url().should('include', '/inventory-item')
    
    //Проверяем наименование и цену внутри карточки товара
    // Тест упадет, так как в карточке товара другой товар
    cy.get('[data-test="inventory-item-name"]').invoke('text').should('equal', 'Sauce Labs Backpack')
    cy.get('[data-test="inventory-item-price"]').invoke('text').should('equal', '$29.99')
  })
})