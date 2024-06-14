class ErrorHandler:
    def handle_error(self, error):
        # Log error
        print(f"Error occurred: {error}")
        # Send email notification or log to ThingsBoard
