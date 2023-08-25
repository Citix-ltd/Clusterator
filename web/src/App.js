import React from 'react'
import './App.css';
import Box from '@mui/material/Box';
import Paper from '@mui/material/Paper';
import Grid from '@mui/material/Grid';
import Button from '@mui/material/Button';
import TextField from '@mui/material/TextField';
import Divider from '@mui/material/Divider';



const ENDPOINT = "http://127.0.0.1:3000";

function Image(props) {
  console.log(props)
  return <div onClick = {props.onClick}>
    <img src = {ENDPOINT + "/file/" + props.class +"/" + props.filename}></img>
  </div>
}



function App(){
  const [classes, setClasses] = React.useState([]);
  const [ungrouped, setUngrouped] = React.useState([]);
  const [cls, setCls] = React.useState("");
  const [selected, setSelected] = React.useState([]);
  const classRef = React.useRef('')

  React.useEffect(() => {
    fetch(ENDPOINT + "/classes").then(response => response.json()).then(
      data => {setClasses(data["classes"]); setCls(data["classes"][0]["class"])}
    )
  }, [])

  React.useEffect(() => {
    fetch(ENDPOINT + "/classes/Ungrouped").then(response => response.json()).then(
      data => setUngrouped(data["filenames"])
    )
  }, [])

  return (
    <div className='main'> 
    <div className="menu">
      <Button variant="contained" 
        onClick ={()=>{const class_name = classRef.current.value;
          fetch(ENDPOINT + "/class/" + class_name, {
            method : 'post'
          })
          setClasses([...classes, {class : class_name, preview: null}]);
          setCls(class_name);
          }}>
          Create
      </Button>
      <TextField inputRef = {classRef} id="outlined-basic" label="Outlined" variant="outlined" />
      <Button variant="contained"
        onClick = {() => {
            fetch(ENDPOINT + "/move", {
              method : "post",
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ files: selected.map((i) => {return {"file" : i}}), class : cls})
            }).then(() => {

              fetch(ENDPOINT + "/classes").then(response => response.json()).then(
                data => {setClasses(data["classes"]); setCls(data["classes"][0]["class"])}
              )
              setSelected([]);
              }
            )
        }}
      >Move</Button>
    </div>
    <Divider orientation="vertical" flexItem />
    <div className='gallery'>
      <h2>Gallery</h2>
      <div className ="flex-wrap">
        {
          classes.map((x) => {
            return <div key = {x.class}  onClick = {
              () => {
                console.log(x);
                setCls(x.class)
              }
            }>
              {x.class === cls?<b>{x.class}</b>:x.class}
              <Image 
                class = {x.class}
                filename = {x.preview}
               
              />
            </div>
          })
        }
      </div>
    </div>
    <Divider orientation="vertical" flexItem />
    <div className='ungrouped'>
      <h2>Ungrouped</h2>
      <div className ="flex-wrap">
      {
        selected.map((x) => {
          return (
            <div 
              key = {x}
             >
            <Image class = "Ungrouped" filename = {x}/>

          </div>)
        })
      }
      </div>
      <Divider flexItem />
      <div className ="flex-wrap">
      {
        
        ungrouped.map((x) => {
          return (
            <div key = {x}
              onClick = {
                () => {
                  if (!selected.includes(x)) {
                    setSelected([...selected, x])
                  }
                  setUngrouped(ungrouped.filter((i) => {return i != x}));
                  fetch(ENDPOINT + "/sort", {
                    method: 'post',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ files: selected})
                  }).then(response => response.json()).then(
                    data => setUngrouped(data["files"].filter((i) => {
                      return !selected.includes(i["file"]) && i["file"] != x
                    }).map((i) => {
                      return i["file"]
                    }))
                  )
                }
              }
              
             >
            <Image class = "Ungrouped" filename = {x}/>

          </div>)
        })
      }
      </div>
    </div>

    </div>
  );
 
}

export default App;
