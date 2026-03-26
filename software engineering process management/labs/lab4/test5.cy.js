describe('Сортировка', () => {
  it('Изменяем порядок сортировки, проверяем изменения в первом и последнем элементах', () => {

    // Открываем сайт
    cy.visit('https://www.saucedemo.com/')

    // Авторизуемся
    cy.get('[data-test="username"]').type('standard_user', {delay: 200})
    cy.get('[data-test="password"]').type('secret_sauce', {delay: 200})
    cy.get('[data-test="login-button"]').click()
    cy.wait(1000)

    // Проверяем, что url изменился
    cy.url().should('include', '/inventory')

    // Проверяем, что наименование первого предмета 'Sauce Labs Backpack' и цена '$29.99' 
    cy.get('[data-test="inventory-item-name"]').eq(0).invoke('text').should('equal', 'Sauce Labs Backpack')
    cy.get('[data-test="inventory-item-price"]').eq(0).invoke('text').should('equal', '$29.99')
    cy.wait(1000)

    // Меняем сортировку на от Я до А
    cy.get('[data-test="product-sort-container"]').select('Name (Z to A)')
    cy.wait(1000)

    // Проверяем, что наименование первого предмета изменилось 'Test.allTheThings() T-Shirt (Red)' и цена '$15.99' 
    cy.get('[data-test="inventory-item-name"]').eq(0).invoke('text').should('equal', 'Test.allTheThings() T-Shirt (Red)')
    cy.get('[data-test="inventory-item-price"]').eq(0).invoke('text').should('equal', '$15.99')
    cy.wait(1000)

    // Проверяем, что наименование последнего предмета 'Sauce Labs Backpack' и цена '$29.99' 
    cy.get('[data-test="inventory-item-name"]').eq(5).invoke('text').should('equal', 'Sauce Labs Backpack')
    cy.get('[data-test="inventory-item-price"]').eq(5).invoke('text').should('equal', '$29.99')
  })
})