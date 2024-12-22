import asyncio
import websockets
import json

async def main():
    uri = 'ws://10.120.222.229:6789'
    async with (websockets.connect(uri) as websocket):
        player = True
        while True:
            try:
                data = await websocket.recv()
                message = json.loads(data)
                if message['type'] == 'waiting':
                    print(message['message'])
                elif message['type'] == 'start':
                    player = message['player']
                    print(message['message'])
                elif message['type'] == 'your_move':
                    print(message['message'])
                    move = input()
                    while move not in ['Камень', 'Ножницы', 'Бумага']:
                        print("Пожалуйста, перепроверь свой ввод!")
                        print('Камень - если выбрали камень.')
                        print('Ножницы - если выбрали ножницы')
                        print('Бумага - если выбрали бумагу.')
                    await websocket.send(json.dumps({'move' : move}))
                elif message['type'] == 'result':
                    move1 = message['move1']
                    move2 = message['move2']
                    result = message['result']
                    print(f'Первый игрок выбрал {move1}')
                    print(f'Второй игрок выбрад {move2}')
                    if player == 'player1':
                        print(f'Ваш ход: {move1}, ход соперника: {move2}.')
                        if result == 'draw':
                            print('Ничья!')
                        elif result == 'player1':
                            print('Вы выиграли!')
                        else:
                            print('Вы проиграли. Skill issue!')
                    if player == 'player2':
                        print(f'Ваш ход: {move2}, ход соперника: {move1}.')
                        if result == 'draw':
                            print('Ничья!')
                        elif result == 'player1':
                            print('Вы проиграли. Skill issue!')
                        else:
                            print('Вы выиграли!')
                elif message['type'] == 'error':
                    print('Ошибка:', message['message'])
                    break
                elif message['type'] == 'rematch':
                    print(message['message'])
                    move = input().strip()
                    while move not in ['Да', 'Нет']:
                        print("Пожалуйста, перепроверь свой ввод!")
                        print('Если хотите сыграть еще раз, введите "Да".')
                        print('Если хотите закончить игру, введите "Нет".')
                    await websocket.send(json.dumps({'response': move}))
                elif message['type'] == 'end':
                    print(message['message'])
                    break
                else:
                    print(message['message'])
                    break
            except Exception as error:
                print('Ошибка:', error)
                break

if __name__ == '__main__':
    asyncio.run(main())