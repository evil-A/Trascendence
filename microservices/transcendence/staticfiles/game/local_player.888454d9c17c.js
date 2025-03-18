class Player
{
    constructor(position, canvas, human = true){
        this.height = canvas.height *.2;
        this.width = canvas.width*.02;
        this.speed = canvas.height*.01;
        this.canvas_height = canvas.height;
        this.x = position ? 0 : canvas.width - this.width;
        this.y = (this.canvas_height - this.height) / 2;
        this.previous_position = this.y;
    }
    move(states, ai){
        let direction = 0
        if (this.x)
        {
            if (states['ArrowUp']){direction -= 1}
            if (states['ArrowDown']){direction += 1}
        }
        else if(!ai)
        {
            if (states['w']){direction -= 1}
            if (states['s']){direction += 1}
        }
        this.previous_position = this.y;
        this.y += direction*this.speed;
        this.y = Math.max(0, Math.min(this.y, this.canvas_height - this.height));
    }

    draw(context)
    {
        context.fillRect(this.x, this.y, this.width, this.height);
    }
}

export default Player;