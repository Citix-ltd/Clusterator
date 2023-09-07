import React, { Component, FunctionComponent } from 'react'
import SelectionArea, { SelectionEvent } from '@viselect/react';
import './App.css';
import Button from '@mui/material/Button';
import TextField from '@mui/material/TextField';
import Divider from '@mui/material/Divider';



const ENDPOINT = "http://127.0.0.1:3001";

interface ImageProps {
  label: string;
  isSelected?: boolean;
  filename?: string;
  onClick?: () => void;
}

class Image extends Component<ImageProps> {
  render() {
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

    let imgSrc: string;
    if (this.props.filename == null) {
      imgSrc = "/icon-image-placeholder.svg";
    } else {
      imgSrc = ENDPOINT + "/file/" + this.props.label + "/" + this.props.filename;
    }

    return (
      <div onClick={this.props.onClick} style={containerStyle}>
        <img
          style={imageStyle}
          src={imgSrc}
          alt="Image"
          draggable="false"
        />
      </div>
    );
  }
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
  const [annotated, setAnnotated] = React.useState<string[]>([]);
  const [selected, setSelected] = React.useState<Set<string>>(() => new Set());
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
      body: JSON.stringify({ files: annotated })
    }).then(response => response.json()).then(
      data => setUngrouped(data["files"])
    )
  }, [annotated]);
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
    if (activeClass === null) {
      return;
    }
    fetch(ENDPOINT + "/move", {
      method: "post",
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ files: annotated, class: activeClass?.name })
    }).then(() => {
      fetch(ENDPOINT + "/classes").then(response => response.json()).then(
        data => { setClasses(data["classes"]); setActiveClass(data["classes"][0]["class"]) }
      )
      setAnnotated([]);
    })
  }
  const handleKeyPress = (event: React.KeyboardEvent<HTMLDivElement>) => {
    if (event.key !== 'Enter') return;
    const newAnnotated = [...annotated, ...Array.from(selected)];
    setAnnotated(newAnnotated);
    setSelected(new Set());
  };
  function onUngroupedClicked(filename: string) {
    if (annotated.includes(filename)) {
      return;
    }
    setAnnotated([...annotated, filename])
    setUngrouped(ungrouped.filter((i) => { return i != filename }));
  }

  /*
    Selection
  */
  const extractIds = (els: Element[]): string[] =>
    els.map(v => v.getAttribute('data-key'))
      .filter(Boolean)
      .map(String);
  const onStart = ({ event, selection }: SelectionEvent) => {
    if (!event?.ctrlKey && !event?.metaKey) {
      selection.clearSelection();
      setSelected(() => new Set());
    }
  };
  const onMove = ({ store: { changed: { added, removed } } }: SelectionEvent) => {
    setSelected(prev => {
      const next = new Set(prev);
      extractIds(added).forEach(id => next.add(id));
      extractIds(removed).forEach(id => next.delete(id));
      return next;
    });
  };

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
                  label={x.name}
                  filename={x.preview}
                />
              </div>
            })
          }
        </div>
      </div>
      <Divider orientation="vertical" flexItem />
      <div className='ungrouped' onKeyDown={handleKeyPress} tabIndex={0}>
        <h2>Staged</h2>
        <div className="flex-wrap">
          {
            annotated.map((x) => {
              return (
                <div key={x}>
                  <Image label="Ungrouped" filename={x} />
                </div>)
            })
          }
        </div>
        <Divider flexItem />
        <h2>Ungrouped</h2>
        <SelectionArea
          className="flex-wrap selectable-container"
          onStart={onStart}
          onMove={onMove}
          selectables=".selectable"
        >
          {
            ungrouped.map((x) => {
              return (
                <div
                  className={selected.has(x) ? 'selected selectable' : 'selectable'}
                  key={x}
                  data-key={x}
                >
                  <Image label="Ungrouped" filename={x} />
                </div>)
            })
          }
        </SelectionArea>
      </div>
    </div>
  );

}

export default App;
