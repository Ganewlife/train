function updateCommande(commandeId, currentStatus) {
    const checkbox = document.getElementById("switch-" + commandeId);

    const transitions = {
        "ASSIGNEE": "EN_COURS",
        "EN_COURS": "CONFIRMEE",
        "CONFIRMEE": "LIVREE"
    };

    const nextStatus = transitions[currentStatus];

    if (!nextStatus) return;

    fetch(`/commande/${commandeId}/status/`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie("csrftoken")
        },
        body: JSON.stringify({
            status: nextStatus
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            checkbox.disabled = true;
            setTimeout(() => window.location.reload(), 200);
        } else {
            checkbox.checked = false;
            alert(data.error || "Erreur");
        }
    })
    .catch(() => {
        checkbox.checked = false;
    });
}

// CSRF helper
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie) {
        document.cookie.split(';').forEach(cookie => {
            cookie = cookie.trim();
            if (cookie.startsWith(name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
            }
        });
    }
    return cookieValue;
}