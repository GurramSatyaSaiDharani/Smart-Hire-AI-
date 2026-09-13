function logout() {

    localStorage.removeItem("token");

    alert("Logged out Successfully");

    window.location.href = "login.html";

}