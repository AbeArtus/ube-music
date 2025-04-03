import './particle.css';

export const CreateParticle = (x: number, y: number) => {
    // Create a custom particle element
    const particle = document.createElement('particle');
    particle.style.opacity = '0';

    // Set the initial position of the particle
    particle.style.left = `${x}px`;
    particle.style.top = `${y}px`;

    // Calculate a random size from 5px to 25px
    const size = Math.floor(Math.random() * 5 + 4);
    // Apply the size on each particle
    particle.style.width = `${size}px`;
    particle.style.height = `${size}px`;
    // Generate a random color in a blue/purple palette
    particle.style.background = 'white';

    // Calculate the destination position
    const destinationX = x + (Math.random() * 2 - 1) * 2 * 40;
    const destinationY = y + (Math.random() * 2 - 1) * 2 * 40;

    // Store the animation in a variable because we will need it later
    const animation = particle.animate([
        {
            // set to smallest size
            width: `1px`,
            blur: `100px`,
            height: `1px`,
        },
        {
            // Set the origin position of the particle
            // We offset the particle with half its size to center it around the mouse
            transform: `translate(-${size / 2}px, -${size / 2}px)`,
            blur: `50px`,
            opacity: .8
        },
        {
            // We define the final coordinates as the second keyframe
            transform: `translate(${destinationX - x}px, ${destinationY - y}px)`,
            blur: `0px`,
            opacity: 0
        }
    ], {
        // Set a random duration from 500 to 1500ms
        duration: 1500 + Math.random() * 1000,
        // easing: 'cubic-bezier(0, .9, .57, 1)',
        // Delay every particle with a random value from 0ms to 200ms
        // delay: Math.random() * 200
    });
    // Append the element into the body
    document.body.appendChild(particle);

    // Remove the particle after the animation finishes
    animation.onfinish = () => {
        particle.remove();
    };
};