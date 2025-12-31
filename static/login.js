
function togglePassword(){
    let passwordField = document.getElementById("password");
    if(passwordField.type ==="password"){
        passwordField.type = "text";
    } else{
        passwordField.type = "password"
    }
}

