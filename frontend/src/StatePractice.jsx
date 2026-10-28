// import { useState } from "react";

// function StatePractice() {
//     const [count , updatedCount] = useState(0)

//     return (
//         <div>
//             <h2>Count</h2>
//             <p>Current Count : {count}</p>

//             <button onClick={() => updatedCount(count + 1)}>
//                 Click to Increase
//             </button>

//             <button onClick={() => updatedCount(count - 1)}>
//                 Click to Decrease
//             </button>
//         </div>
//     )
// }

// export default StatePractice;

// function ListPractice() {
//     const names = ["Ali", "Sara", "Ahmed"];

//     return (
//         <div>
//             <h2>Names</h2>
//             {names.map((name) => (
//                 <p key={name}>Name :{name}</p>
//             ))}
//         </div>
//     );
// }

// export default ListPractice;

import { useState } from "react";

function InputPractice() {
    const [ name , setName ] = useState("");

    return (
        <div>
            <h2>Input Practice</h2>

            <input
                type="text"
                placeholder="Enter your name"
                value={name}
                onChange={(event) => setName(event.target.value)}
            />

            <p>Your name: {name}</p>
            
        </div>
    )
}

export default InputPractice;