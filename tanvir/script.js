let expenses = JSON.parse(localStorage.getItem("expenses")) || [];

const form = document.getElementById("expense-form");
const list = document.getElementById("expense-list");
const totalDisplay = document.getElementById("total");

form.addEventListener("submit", function (e) {
    e.preventDefault();

    const title = document.getElementById("title").value;
    const amount = parseFloat(document.getElementById("amount").value);
    const category = document.getElementById("category").value;
    const date = document.getElementById("date").value;

    const expense = { title, amount, category, date };
    expenses.push(expense);

    localStorage.setItem("expenses", JSON.stringify(expenses));
    form.reset();
    renderExpenses();
});

function renderExpenses() {
    list.innerHTML = "";
    let total = 0;

    expenses.forEach((expense, index) => {
        total += expense.amount;

        const row = document.createElement("tr");
        row.innerHTML = `
            <td>${expense.title}</td>
            <td>${expense.amount}</td>
            <td>${expense.category}</td>
            <td>${expense.date}</td>
            <td>
                <button class="delete-btn" onclick="deleteExpense(${index})">
                    Delete
                </button>
            </td>
        `;
        list.appendChild(row);
    });

    totalDisplay.textContent = total.toFixed(2);
}

function deleteExpense(index) {
    expenses.splice(index, 1);
    localStorage.setItem("expenses", JSON.stringify(expenses));
    renderExpenses();
}

renderExpenses();