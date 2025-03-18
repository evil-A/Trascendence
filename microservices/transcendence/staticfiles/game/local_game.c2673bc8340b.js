import Player from './local_player.js';
import AIPlayer from './aiplayer.js';
import Ball from './ball.js'

class Game{
    constructor(local)
    {
        let ai = !Boolean(local)
        this.canvas = document.getElementById('pongCanvas');
        this.canvas.width = this.canvas.clientWidth
        this.canvas.height = this.canvas.clientHeight
        this.context = this.canvas.getContext('2d')
        this.player1_score = 0;
        this.player2_score = 0;
        this.ai = ai;
        this.resizeCanvas(ai);
        this.gameLoop();
    }

    resizeCanvas(ai)
    {
        this.player1 = ai ? new AIPlayer(this.canvas) : new Player(true, this.canvas, true);
        this.player2 = new Player(false, this.canvas, true);
        this.ball = new Ball(this.canvas);
    }

    draw()
    {
        this.context.clearRect(0, 0, this.canvas.width, this.canvas.height);
        this.context.fillStyle = 'black';
        this.ball.draw(this.context);
        this.player1.draw(this.context);
        this.player2.draw(this.context);
        this.context.font = this.canvas.height *.2 + "px Arial";
        this.context.textAlign = 'center';
        this.context.fillText(this.player1_score, this.canvas.width*.25, this.canvas.height*.5);
        this.context.fillText(this.player2_score, this.canvas.width*.75, this.canvas.height*.5);
    }

    move()
    {
        this.ball.move(this.canvas);
        if (this.ball.speedX < 0 && this.ball.x <= this.player1.width + this.ball.size && this.ball.y >= this.player1.y && this.ball.y <= this.player1.y + this.player1.height)
        {
            this.ball.speedX = -this.ball.speedX + 0.0001*this.canvas.width;
        }
        else if (this.ball.speedX > 0 && this.ball.x > this.canvas.width - this.ball.size - this.player2.width && this.ball.y >= this.player2.y && this.ball.y <= this.player2.y + this.player2.height) 
        {
            this.ball.speedX = -this.ball.speedX - 0.0001*this.canvas.width;
        }
        else if (this.ball.x < 0 || this.ball.x > this.canvas.width)
        {
            this.ball.x > 0 ? this.player1_score++ : this.player2_score++;
            this.ball.resetBall(this.canvas);
        }
        if (this.ai)
        {
            this.player1.calculate_move([this.ball.x, this.ball.y], [this.ball.speedX, this.ball.speedY]);
        }
    }

    end_game()
    {
        this.draw()
        if (this.ai){
            const gameData = {
                score1: this.player1_score,
                score2: this.player2_score,
            };
            let response = fetch("/game/local/save", {
                method: 'POST',
                body: JSON.stringify(gameData)});
        }
        this.player1.removeListener()
        this.player2.removeListener()
        document.getElementById("EndGameModalContent").innerHTML = this.player1_score + " - " + this.player2_score;
        document.getElementById("EndGameModalDialog").showModal()
        document.getElementById("game-board").innerHTML = ""
    }

    gameLoop()
    {
        this.draw();
        this.move();
        if (Math.max(this.player1_score,  this.player2_score) === 10)
        {
            this.end_game();
            return;
        }
        requestAnimationFrame(this.gameLoop.bind(this));
    }
}

function disableNav() {
    const navbarButtons = document.querySelectorAll('.nav-link');
    navbarButtons.forEach(link => {
        link.classList.add('disabled')
    });
}

export function startGame(local){
    disableNav()
    new Game(local);
}