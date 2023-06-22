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

function syncData(data) {
	console.log(data[0], data[1], data[2], data[3])
	ArduinoRelayButton[0].state = parseInt(data[0]) == 0 ? E_OK : E_NOK
	ArduinoRelayButton[1].state = parseInt(data[2]) == 0 ? E_OK : E_NOK
	ArduinoRelayButton[2].state = parseInt(data[1]) == 0 ? E_OK : E_NOK
	ArduinoRelayButton[3].state = parseInt(data[3]) == 0 ? E_OK : E_NOK
	payload = {
		button: ArduinoRelayButton[0].button.split("_")[0],
		response: ArduinoRelayButton[0].state,
	}
	setArduinoRelayButtonStateAndColor(payload)
	payload = {
		button: ArduinoRelayButton[1].button.split("_")[0],
		response: ArduinoRelayButton[1].state,
	}
	setArduinoRelayButtonStateAndColor(payload)
	payload = {
		button: ArduinoRelayButton[2].button.split("_")[0],
		response: ArduinoRelayButton[2].state,
	}
	setArduinoRelayButtonStateAndColor(payload)
	payload = {
		button: ArduinoRelayButton[3].button.split("_")[0],
		response: ArduinoRelayButton[3].state,
	}
	setArduinoRelayButtonStateAndColor(payload)
}

function setArduinoRelayButtonStateAndColor(response) {
	// console.log(response)
	let buttonName = response.button
	let responseState = response.response
	const matchingState = states.find((state) => state.state === responseState)
	if (matchingState) {
		$("#" + buttonName + "_button, #" + buttonName + "_label").css(
			"color",
			matchingState.color,
		)
	}
}
