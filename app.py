from flask import Flask, request, jsonify
from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler, AbstractExceptionHandler
from ask_sdk_core.utils import is_request_type, is_intent_name
from ask_sdk_webservice_support.webservice_handler import WebserviceSkillHandler
import google.generativeai as genai

app = Flask(__name__)

# ✅ PASTE YOUR GEMINI API KEY HERE
GEMINI_API_KEY = "AQ.Ab8RN6JYt8zZgdZTyGwA2loTIsk7BJvBeDhNTjExnEsBjG3LjQ"

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")


class LaunchRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        speak = "Gemini is ready. What would you like to ask?"
        return handler_input.response_builder.speak(speak).ask(speak).response


class GeminiQueryIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("GeminiQueryIntent")(handler_input)

    def handle(self, handler_input):
        slots = handler_input.request_envelope.request.intent.slots
        user_query = slots["query"].value if slots.get("query") else "Hello"

        try:
            response = model.generate_content(
                f"Answer in under 100 words, plain spoken English only, no bullet points, no markdown: {user_query}"
            )
            speak = response.text
        except Exception as e:
            speak = "Sorry, I could not reach Gemini right now. Please try again."

        return handler_input.response_builder.speak(speak).ask("Any other question?").response


class HelpIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        speak = "Ask me any question and I will answer using Gemini AI."
        return handler_input.response_builder.speak(speak).ask(speak).response


class StopIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return (is_intent_name("AMAZON.CancelIntent")(handler_input) or
                is_intent_name("AMAZON.StopIntent")(handler_input))

    def handle(self, handler_input):
        return handler_input.response_builder.speak("Goodbye!").response


class SessionEndedHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        return handler_input.response_builder.response


class ErrorHandler(AbstractExceptionHandler):
    def can_handle(self, handler_input, exception):
        return True

    def handle(self, handler_input, exception):
        speak = "Sorry, something went wrong. Please try again."
        return handler_input.response_builder.speak(speak).ask(speak).response


sb = SkillBuilder()
sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(GeminiQueryIntentHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(StopIntentHandler())
sb.add_request_handler(SessionEndedHandler())
sb.add_exception_handler(ErrorHandler())

skill_handler = WebserviceSkillHandler(skill=sb.create())


@app.route("/alexa", methods=["POST"])
def alexa_skill():
    response = skill_handler.verify_request_and_dispatch(
        request.headers, request.data.decode("utf-8")
    )
    return jsonify(response)


@app.route("/")
def health():
    return "Alexa Gemini Skill is running!", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
