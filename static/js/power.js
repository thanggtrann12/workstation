var powerState = E_NOK
const PowerButtons = [
	{ button: "power_button", label: "power_label", state: powerState },
	{ button: "set_voltage_button", label: "SET", state: "" },
]
function monitorPowerButtonsClick(button) {
	const buttonElement = $("#" + button.button)
	buttonElement.on("click", function () {
		if (button.label !== "SET") {
			button.state = !button.state
			socket.emit(`set_power_to_${button.state == E_OK ? "on" : "off"}`)
		} else {
			console.log(button.button)
			if (parseInt($("#input_voltage").val()) > 0) {
				console.log("valid")
			} else console.log(parseInt($("#input_voltage").val()))
		}
	})
}
