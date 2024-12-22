import asyncio
import websockets
import json

async def game_loop(game):
    while not game.game_over:
        await game.player1_ws.send(
            json.dumps(
                {
                    'type': 'your_move',
                    'message': 'Введите ваш ход (Камень, Ножницы или Бумага):',
                }
            )
        )
        await game.player2_ws.send(
            json.dumps(
                {
                    'type': 'your_move',
                    'message': 'Введите ваш ход (камень, ножницы или бумага):',
                }
            )
        )
        receive_moves = [
            game.receive_move(game.player1_ws),
            game.receive_move(game.player2_ws),
        ]
        results = await asyncio.gather(*receive_moves)
        if not all(results):
            await game.broadcast(
                {
                    'type': 'error',
                    'message': 'Игрок отключился или сделал недопустимый ход.',
                }
            )
            break
        await game.determine_winner()

async def start_game(game):
    await game.player1_ws.send(
        json.dumps(
            {
                "type": "start",
                "player": "player1",
                "message": "Игра началась. Вы - Игрок 1",
            }
        )
    )
    await game.player2_ws.send(
        json.dumps(
            {
                "type": "start",
                "player": "player2",
                "message": "Игра началась. Вы - Игрок 2",
            }
        )
    )
    await game_loop(game)

class Game:
    def __init__(self, player1_ws, player2_ws):
        self.players = {player1_ws: None, player2_ws: None}
        self.player1_ws = player1_ws
        self.player2_ws = player2_ws
        self.game_over = False
    async def receive_move(self, websocket):
        try:
            data = await websocket.recv()
            message = json.loads(data)
            move = message.get('move')
            if move not in ['Камень', 'Ножницы', 'Бумага']:
                await websocket.send(json.dumps({'type': 'error', 'message': 'Недопустимый ход'}))
                return False
            self.players[websocket] = move
            return True
        except websockets.ConnectionClosedError:
            print('Соединение закрыто(receive_move)')
            return False
    async def receive_response(self, websocket):
        try:
            data = await websocket.recv()
            message = json.loads(data)
            response = message.get('response')
            if response not in ['Да', 'Нет']:
                await websocket.send(json.dumps({'type': 'error', 'message': 'Недопустимый ответ'}))
                return False
            return response == 'Да'
        except websockets.ConnectionClosedError:
            print('Соединение закрыто(receive_response)')
            return False
    def get_result(self, move1, move2):
        if move1 == move2:
            return 'draw'
        elif (move1 == 'Камень' and move2 == 'Ножницы') or \
             (move1 == 'Ножницы' and move2 == 'Бумага') or \
             (move1 == 'Бумага' and move2 == 'Камень'):
            return 'player1'
        else:
            return 'player2'
    async def broadcast(self, message):
        await self.player1_ws.send(json.dumps(message))
        await self.player2_ws.send(json.dumps(message))
    async def reset_game(self):
        self.players[self.player1_ws] = None
        self.players[self.player2_ws] = None
        self.game_over = False

    async def ask_for_rematch(self):
        await self.broadcast({'type': 'rematch', 'message': 'Хотите сыграть Снова? (Да/Нет)'})
        receive_responses = [self.receive_response(self.player1_ws), self.receive_response(self.player2_ws)]
        results = await asyncio.gather(*receive_responses)
        if all(results):
            await self.reset_game()
            game = Game(self.player1_ws, self.player2_ws)
            await start_game(game)
        else:
            await self.broadcast({'type': 'rematch', 'message': 'Игра завершена'})
    async def detemine(self):
        move1 = self.players[self.player1_ws]
        move2 = self.players[self.player2_ws]
        result = self.get_result(move1, move2)
        await self.broadcast({'type': 'result', 'move1': move1, 'move2': move2, 'result': result})
        await self.ask_for_rematch()
        self.game_over = True

waiting_players = []

async def handler(websocket):
    print('Новое соединение')
    try:
        if waiting_players:
            opponent_ws = waiting_players.pop(0)
            game = Game(opponent_ws, websocket)
            await start_game(game)
        else:
            waiting_players.append(websocket)
            await websocket.send(json.dumps({'type': 'waiting', 'message': 'Ожидание соперника...'}))
            await websocket.wait_closed()
    except websockets.exceptions.ConnectionClosed:
        print('Соединение закрыто(handler)')
    finally:
        if websocket in waiting_players:
            waiting_players.remove(websocket)

async def main():
    async with websockets.serve(handler, "10.120.222.229", 6789):
        print("Сервер запущен на ws://10.120.222.229:6789")
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())