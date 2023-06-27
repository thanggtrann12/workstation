let isLock = false
let isAdmin = false
function adminSetting(admin_id) {
	console.log(session_id, admin_id)
	if (session_id.includes(admin_id)) {
		$("#user_name").text(admin_id)
		isAdmin = true
	} else {
		isAdmin = false
		$("#user_name").text("GUESS")
		$("#lock_button").text("Force Unlock")
	}
}

function setLock(locked) {
	console.log("lock", locked)
	if (locked) {
		lockComponent()
	} else unLockComponent()
}
function lockComponent() {
	if (!isAdmin) {
		console.log("log")
		$("[id]").addClass("disable-click")
	} else {
		$("#lock_button").text("Unlock")
	}
}

function unLockComponent() {
	console.log("unlog")
	$("[id]").removeClass("disable-click")
}
