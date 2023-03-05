"""
上面的代码实现了一个简单的责任链模式，其中有两个处理器 ConcreteHandlerA 和 ConcreteHandlerB。
当请求传递给某个处理器时，它会试图处理请求。
如果处理器不能处理请求，它将请求传递给下一个处理器，直到有一个处理器处理了请求为止。
"""


class Handler:
    def __init__(self, success=None):
        self.success = success

    def handle_request(self, request):
        if self.success:
            self.success.handle_request(request)
        else:
            self.process_request(request)

    def process_request(self, request):
        pass


class ConcreteHandlerA(Handler):
    def process_request(self, request):
        if request == "A":
            print("Request handled by ConcreteHandlerA")
        else:
            super().process_request(request)


class ConcreteHandlerB(Handler):
    def process_request(self, request):
        if request == "B":
            print("Request handled by ConcreteHandlerB")
        else:
            super().process_request(request)


# Create the handler objects
handler_a = ConcreteHandlerA()
handler_b = ConcreteHandlerB(handler_a)

# Send requests to the handlers
handler_b.handle_request("A")
handler_b.handle_request("B")
handler_b.handle_request("C")
