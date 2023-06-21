$(document).ready(function () {
	$("#command_entry").on("input", function () {
		ttfis_cmd = $(this).val().toUpperCase()
	})
	$("#command_entry").on("keydown", function (event) {
		doAutoComplete(event)
	})
	$("#standby_buton").on("click", function () {
		standby_test()
	})
	$("#shutdown_buton").on("click", function () {
		shutdown_test()
	})
	$("#set_test_time").on("click", () => {
		setTestTime()
	})
	ArduinoRelayButton.forEach(monitorArduinoRelayButtonClick)
	TargetButtons.forEach(monitorTargetbuttonsClick)
	PowerButtons.forEach(monitorPowerButtonsClick)
})
