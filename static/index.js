document.addEventListener("DOMContentLoaded", () => {

    const saveBtn = document.getElementById("save-button")
    saveBtn? saveBtn.addEventListener("click", () => {
        const favouriteForm = document.getElementById("favourite")
        console.log(favouriteForm)
    }): console.log("not in stock_valuation table");

    let yearCount = 1;

    document.getElementById('add-year')? document.getElementById('add-year').addEventListener('click', () => {
        yearCount++;
        const newYearDiv = document.createElement('div');
        newYearDiv.classList.add('mb-3', 'row');
        newYearDiv.innerHTML = `
            <label for="year-${yearCount}" class="col-sm-2 col-form-label">Year ${yearCount}</label>
            <div class="col-sm-4">
                <input type="number" class="form-control" id="year-${yearCount}" name="year-${yearCount}" placeholder="Enter dividend return" step="0.01" required>
            </div>
        `;
        document.getElementById('dividend-entries').appendChild(newYearDiv);
    }): console.log("not in calculator");


    const logOutBtn = document.getElementById("logout")

    logOutBtn.addEventListener("click", () => {
        if (confirm("Are you sure you want to continue?")) {
            window.location.href = "/logout"; 
        }
    })
})