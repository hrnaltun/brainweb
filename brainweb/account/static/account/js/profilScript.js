document.addEventListener("DOMContentLoaded", function() {
    showProfileForm(); // Sayfa yüklendiğinde profil düzenleme formunu göster
});

let selectedElement = null;

function showProfileForm() {
    document.getElementById("profileForm").style.display = "block";
    document.getElementById("userDetails").style.display = "none";
    document.getElementById("changePasswordForm").style.display = "none";
    document.getElementById("deleteAccountForm").style.display = "none";
    updateSelectedLinkStyle("profileLink");
}

function showUserDetails() {
    document.getElementById("profileForm").style.display = "none";
    document.getElementById("userDetails").style.display = "block";
    document.getElementById("changePasswordForm").style.display = "none";
    document.getElementById("deleteAccountForm").style.display = "none";
    updateSelectedLinkStyle("userDetailsLink");
}

function showChangePasswordForm() {
    document.getElementById("profileForm").style.display = "none";
    document.getElementById("userDetails").style.display = "none";
    document.getElementById("changePasswordForm").style.display = "block";
    document.getElementById("deleteAccountForm").style.display = "none";
    updateSelectedLinkStyle("changePasswordLink");
}

function showDeleteAccountForm() {
    document.getElementById("profileForm").style.display = "none";
    document.getElementById("userDetails").style.display = "none";
    document.getElementById("changePasswordForm").style.display = "none";
    document.getElementById("deleteAccountForm").style.display = "block";
    updateSelectedLinkStyle("deleteAccountLink");
}

function updateSelectedLinkStyle(selectedLinkId) {
    var links = document.querySelectorAll(".sidebar ul li a");
    links.forEach(function(link) {
        link.classList.remove("active");
    });
    document.getElementById(selectedLinkId).classList.add("active");
}