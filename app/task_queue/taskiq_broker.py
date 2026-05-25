from taskiq import SimpleRetryMiddleware, TaskiqMessage, TaskiqMiddleware, TaskiqResult
import taskiq_fastapi
from taskiq_aio_pika import AioPikaBroker


class CatchErrorMiddleware(TaskiqMiddleware):
    async def on_error(
        self,
        message: TaskiqMessage,
        result: TaskiqResult,
        exception: BaseException,
    ) -> None:
        print("***********************************************")
        print(f"[TASKIQ ERROR] Ошибка в задаче {message.task_name}:")
        print(message.labels)
        print(str(exception))
        print("***********************************************")


RABBITMQ_URL = "amqp://guest:guest@localhost:5672//"

broker = AioPikaBroker(
    url=RABBITMQ_URL,
).with_middlewares(SimpleRetryMiddleware(default_retry_count=2), CatchErrorMiddleware())

taskiq_fastapi.init(broker, "app.main:app")
