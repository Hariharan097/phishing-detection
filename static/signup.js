// start of nav
function toggleMenu(event) {
    const menu = document.getElementById("side-menu");
    menu.classList.toggle("show");
    event.stopPropagation();
    document.body.addEventListener("click", closeMenu);
}

function closeMenu(event) {
    const menu = document.getElementById("side-menu");

    if (!menu.contains(event.target)) {
        menu.classList.remove("show");
        document.body.removeEventListener("click", closeMenu);
    }
}
// end of nav


// Function to handle the signup button click
function handleSignup() {
    // Log to the console to check if the function is triggered
    console.log("Signup button clicked");

    // Get form data
    const fullname = document.getElementById('fname').value;
    const username = document.getElementById('uname').value;
    const password = document.getElementById('pass').value;
    const confirmpassword = document.getElementById('cpass').value;

    // Validation: Check if passwords match
    if (password !== confirmpassword) {
        alert("Passwords do not match!");
        return;
    }

    // Check if all fields are filled
    if (!fullname || !username || !password || !confirmpassword) {
        alert("Please fill in all fields!");
        return;
    }

    // Log form data (for debugging purposes)
    console.log(`Fullname: ${fullname}, Username: ${username}, Password: ${password}`);

    // Optionally, submit data to the server using AJAX (fetch or XMLHttpRequest)
    // For now, just log success message
    alert("Successfully Registered (But this part needs server-side processing)");
}
