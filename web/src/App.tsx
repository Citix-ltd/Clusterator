import React from 'react'
import './App.css';
import Box from '@mui/material/Box';
import Paper from '@mui/material/Paper';
import Grid from '@mui/material/Grid';
import Button from '@mui/material/Button';
import TextField from '@mui/material/TextField';
import Divider from '@mui/material/Divider';



const ENDPOINT = "http://127.0.0.1:3001";

interface ImageProps {
  onClick?: () => void;
  class: string;
  filename?: string;
}
function Image(props: ImageProps) {
  const containerStyle = {
    width: 128,
    height: 128,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    overflow: 'hidden',
  };

  const imageStyle = {
    maxWidth: '100%',
    maxHeight: '100%',
    display: 'block',
  };

  return (
    <div onClick={props.onClick} style={containerStyle}>
      <img
        style={imageStyle}
        src={ENDPOINT + "/file/" + props.class + "/" + props.filename}
        alt="Image"
      />
    </div>
  );
}


interface LabelClass {
  name: string;
  preview?: string;
}
interface LabelClassResponse {
  classes: LabelClass[];
}
interface FilesResponse {
  files: string[];
}



function App() {
  const [classes, setClasses] = React.useState<LabelClass[]>([]);
  const [ungrouped, setUngrouped] = React.useState<string[]>([]);
  const [activeClass, setActiveClass] = React.useState<LabelClass | null>(null);
  const [selected, setSelected] = React.useState<string[]>([]);
  const inputClassName = React.useRef<HTMLInputElement>();

  /*
    Initial load
  */
  React.useEffect(() => {
    fetch(ENDPOINT + "/classes").then(response => response.json()).then(json => {
      const data = json as LabelClassResponse;
      setClasses(data.classes);
      if (data["classes"].length > 0) {
        setActiveClass(data.classes[0])
      }
    }
    )
  }, [])
  React.useEffect(() => {
    fetch(ENDPOINT + "/classes/Ungrouped").then(response => response.json()).then(json => {
      const data = json as FilesResponse;
      setUngrouped(data.files);
    })
  }, [])

  /*
    Actions
  */
  React.useEffect(() => {
    fetch(ENDPOINT + "/sort", {
      method: 'post',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ files: selected })
    }).then(response => response.json()).then(
      data => setUngrouped(data["files"])
    )
  }, [selected]);
  function onCreateNewClassClick() {
    const class_name = inputClassName.current?.value;
    if (class_name === undefined || class_name.length === 0) {
      return;
    }
    fetch(ENDPOINT + "/class/" + class_name, {
      method: 'post'
    })
    const newClass: LabelClass = { name: class_name };
    setClasses([newClass, ...classes]);
    setActiveClass(newClass)
  }
  function onMoveClicked() {
    fetch(ENDPOINT + "/move", {
      method: "post",
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ files: selected.map((i) => { return { "file": i } }), class: activeClass })
    }).then(() => {

      fetch(ENDPOINT + "/classes").then(response => response.json()).then(
        data => { setClasses(data["classes"]); setActiveClass(data["classes"][0]["class"]) }
      )
      setSelected([]);
    })
  }
  function onUngroupedClicked(filename: string) {
    if (selected.includes(filename)) {
      return;
    }
    setSelected([...selected, filename])
    setUngrouped(ungrouped.filter((i) => { return i != filename }));
  }

  return (
    <div className='main'>
      <div className="menu">
        <Button variant="contained" onClick={onCreateNewClassClick}>Create</Button>
        <TextField inputRef={inputClassName} id="outlined-basic" label="Outlined" variant="outlined" />
        <Button variant="contained" onClick={onMoveClicked}>Move</Button>
      </div>
      <Divider orientation="vertical" flexItem />
      <div className='gallery'>
        <h2>Gallery</h2>
        <div className="flex-wrap">
          {
            classes.map((x) => {
              return <div key={x.name} onClick={() => { setActiveClass(x); }}>
                {x.name === activeClass?.name ? <b>{x.name}</b> : x.name}
                <Image
                  class={x.name}
                  filename={x.preview}
                />
              </div>
            })
          }
        </div>
      </div>
      <Divider orientation="vertical" flexItem />
      <div className='ungrouped'>
        <h2>Ungrouped</h2>
        <div className="flex-wrap">
          {
            selected.map((x) => {
              return (
                <div key={x}>
                  <Image class="Ungrouped" filename={x} />
                </div>)
            })
          }
        </div>
        <Divider flexItem />
        <div className="flex-wrap">
          {
            ungrouped.map((x) => {
              return (
                <div key={x} onClick={() => { onUngroupedClicked(x); }}>
                  <Image class="Ungrouped" filename={x} />
                </div>)
            })
          }
        </div>
      </div>

    </div>
  );

}

export default App;
