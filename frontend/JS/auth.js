document.getElementById("loginForm").addEventListener("submit", function(e){

e.preventDefault();

const email = document.getElementById("email").value;
const password = document.getElementById("password").value;

fetch("http://localhost:5000/login",{

method:"POST",
headers:{
"Content-Type":"application/json"
},

body: JSON.stringify({

email:email,
password:password

})

})

.then(response => response.json())
.then(data => {

if(data.success){

alert("Login correcto");

window.location.href = "jobs.html";

}else{

alert("Credenciales incorrectas");

}

})

.catch(error => console.error(error));

});