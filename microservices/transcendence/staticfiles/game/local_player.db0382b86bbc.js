class Player
{
    constructor(position, canvas, human = true){
        this.height = canvas.height *.2;
        this.width = canvas.width*.02;
        this.speed = canvas.height*.02;
        this.canvas_height = canvas.height;
        this.x = position ? 0 : canvas.width - this.width;
        this.y = (this.canvas_height - this.height) / 2;
        this.previous_position = this.y;
        this.handler = this.handle_keys.bind(this)
        if(human){this.setListener()}
    }

    handle_keys(e)
    {
        if (e.key === 'ArrowUp' && this.x){this.move(-1)}
        if (e.key === 'ArrowDown' && this.x){this.move(1)}
        if (e.key === 'w' && !this.x){this.move(-1)}
        if (e.key === 's' && !this.x){this.move(1)}
    }
    
    setListener()
    {
        document.addEventListener('keydown', this.handler)
    }
    
    removeListener(){
        document.removeEventListener('keydown', this.handler)
    }

    move(direction){
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