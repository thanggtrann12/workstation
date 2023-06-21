const states = [
	{ state: E_OK, color: "#A6E22E" },
	{ state: E_NOK, color: "red" },
]

var accState = E_NOK
var wdState = E_NOK
var ignState = E_NOK
var opt2State = E_NOK

const ArduinoRelayButton = [
	{ button: "acc_button", label: "acc_label", state: accState },
	{ button: "wd_button", label: "wd_label", state: wdState },
	{ button: "ign_button", label: "ign_label", state: ignState },
	{ button: "opt2_button", label: "opt2_label", state: opt2State },
]
function monitorArduinoRelayButtonClick(button) {
	const buttonElement = $("#" + button.button)
	buttonElement.on("click", function () {
		button.state = !button.state
		const matchingState = states.find(
			(state) => state.state === button.state,
		)
		if (matchingState) {
			$("#" + button.label + ", #" + button.button).css(
				"color",
				matchingState.color,
			)
			payload = { button: button.button, state: matchingState.state }
			// Send button state to arduino
			socket.emit("request_to_arduino", payload)
			// Get response from arduino
			socket.on("response_from_arduino", (response) => {
				setArduinoRelayButtonStateAndColor(response)
			})
		}
	})
}

function setArduinoRelayButtonStateAndColor(response) {
	for (let buttonIndex = 0; buttonIndex < response.length; buttonIndex++) {
		console.log(parseInt(response[buttonIndex]))
		ArduinoRelayButton[buttonIndex].state =
			parseInt(response[buttonIndex]) == 0 ? E_OK : E_NOK

		const matchingState = states.find(
			(state) => state.state === ArduinoRelayButton[buttonIndex].state,
		)
		if (matchingState) {
			$(
				"#" +
					ArduinoRelayButton[buttonIndex].label +
					", #" +
					ArduinoRelayButton[buttonIndex].button,
			).css("color", matchingState.color)
		}
	}
}
