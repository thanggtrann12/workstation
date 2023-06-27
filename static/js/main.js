$(document).ready(function () {
	$("#command_entry").on("input", function () {
		ttfis_cmd = $(this).val().toUpperCase()
	})
	$("#command_entry").on("keydown", function (event) {
		doAutoComplete(event)
	})
	$("#standby_buton").on("click", async function () {
		$("#acc_button , #acc_label, #ign_button, #ign_label").css("color", "red")
		try {
			await $.get(
				"http://" +
					location.host +
					`/start-test/standby/${
						$("#test_time").val() == "" ? 1 : parseInt($("#test_time").val())
					}`,
			)
		} catch (error) {
			console.error("Error occurred during the GET request:", error)
		}
	})
	$("#shutdown_buton").on("click", async function () {
		$("#acc_button , #acc_label, #ign_button, #ign_label").css("color", "red")
		try {
			await $.get(
				"http://" +
					location.host +
					`/start-test/shutdown/${
						$("#test_time").val() == "" ? 1 : parseInt($("#test_time").val())
					}`,
			)
		} catch (error) {
			console.error("Error occurred during the GET request:", error)
		}
	})
	$("#wakeup_buton").on("click", async () => {
		$("#acc_button , #acc_label, #ign_button, #ign_label").css(
			"color",
			"#A6E22E",
		)
		try {
			await $.post("http://" + location.host + "/wakeup")
		} catch (error) {
			console.error("Error occurred during the GET request:", error)
		}
	})

	$("#record_scc").change(function () {
		if (this.checked) {
			isRecording = true
		} else {
			isRecording = false
			var fileName = `recorded_text_${new Date().toISOString()}.pro`
			var blob = new Blob([recordedText], {
				type: "text/plain;charset=utf-8",
			})
			saveAs(blob, fileName)
		}
	})

	$("#pause_scc").change(function () {
		if (this.checked) {
			isPausing = true
		} else {
			isPausing = false
		}
	})

	$("#clear_scc").click(function () {
		$("#scc_trace").empty()
	})

	$("#export_scc").click(function () {
		console.log("export")
		{
			const text = $("#scc_trace").text()
			let blob = new Blob([text], {
				type: "text/plain",
			})
			let filename = `${new Date().toISOString()}_SCC_Log.pro`
			saveAs(blob, filename)
		}
	})
	function fetchData() {
		fetch("/get_data", {
			method: "GET",
		})
			.then((response) => response.json())
			.then((data) => {
				updataPowerData(data)
			})
			.catch((error) => {})
	}
	$("#log_out_button").on("click", () => {
		window.location.href = "http://" + location.host + "/logout"
	})
	fetchData()
	setInterval(fetchData, 1000)

	function getAdmin() {
		fetch("/admin", {
			method: "GET",
		})
			.then((response) => response.json())
			.then((data) => {
				console.log(data.admin)
				adminSetting(data.admin)
			})
	}
	getAdmin()
	var lockStatus = false
	$("#lock_button").on("click", () => {
		lockStatus = !lockStatus
		socket.emit("lock", lockStatus)
	})
	ArduinoRelayButton.forEach(monitorArduinoRelayButtonClick)
	TargetButtons.forEach(monitorTargetbuttonsClick)
	PowerButtons.forEach(monitorPowerButtonsClick)
})
