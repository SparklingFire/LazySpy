import LazySpy


async def error_searcher(function):
    print('hello')
    async def maintain():
        try:
            print('proceed')
            await function
        except:
            LazySpy.main_gate.terminate_everything()
            LazySpy.main_gate.loop_starter()
    await maintain()
