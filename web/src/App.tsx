import React, { Component, FunctionComponent } from 'react'
import SelectionArea, { SelectionEvent } from '@viselect/react';
import './App.css';
import Button from '@mui/material/Button';
import TextField from '@mui/material/TextField';
import Divider from '@mui/material/Divider';



const ENDPOINT = "http://localhost:3001/api";

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
interface SortedItem {
  n: string;
  s: number;
}
interface FilesResponse {
  files: SortedItem[];
}



function App() {
  const [ungrouped, setUngrouped] = React.useState<SortedItem[]>([]);
  const [classes, setClasses] = React.useState<LabelClass[]>([]);
  const [activeClass, setActiveClass] = React.useState<LabelClass | null>(null);
  const [staged, setAnnotated] = React.useState<string[]>([]);
  const [selected, setSelected] = React.useState<Set<string>>(() => new Set());
  const inputClassName = React.useRef<HTMLInputElement>();

  /*
    Initial load
  */
  function loadRandomUnsorted() {
    fetch(ENDPOINT + "/classes/unsorted").then(response => response.json()).then(json => {
      const data = json as FilesResponse;
      setUngrouped(data.files);
    })
  }
  React.useEffect(() => {
    fetch(ENDPOINT + "/classes").then(response => response.json()).then(json => {
      const data = json as LabelClassResponse;
      setClasses(data.classes);
    })
  }, [])
  React.useEffect(loadRandomUnsorted, [])

  /*
    Actions
  */
  React.useEffect(() => {
    if (!activeClass || staged.length > 0) {
      return;
    }
    if (!activeClass.preview) {
      loadRandomUnsorted();
      return;
    }
    fetch(ENDPOINT + "/sort_by_class", {
      method: 'post',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ class: activeClass.name })
    }).then(response => response.json()).then(
      data => setUngrouped(data["files"])
    )
  }, [activeClass]);
  React.useEffect(() => {
    if (staged.length === 0) {
      return;
    }
    fetch(ENDPOINT + "/sort", {
      method: 'post',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ files: staged })
    }).then(response => response.json()).then(
      data => setUngrouped(data["files"])
    )
  }, [staged]);
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
      body: JSON.stringify({ files: staged, class: activeClass?.name })
    }).then(() => {
      fetch(ENDPOINT + "/classes").then(response => response.json()).then(
        data => { setClasses(data["classes"]); setActiveClass(data["classes"][0]["class"]) }
      )
      setAnnotated([]);
    })
  }
  const handleKeyPress = (event: React.KeyboardEvent<HTMLDivElement>) => {
    if (event.key !== 'Enter') return;
    const newAnnotated = [...staged, ...Array.from(selected)];
    setAnnotated(newAnnotated);
    setSelected(new Set());
  };

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
            staged.map((x) => {
              return (
                <div key={x}>
                  <Image label="unsorted" filename={x} />
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
                  className={selected.has(x.n) ? 'selected selectable' : 'selectable'}
                  key={x.n}
                  data-key={x.n}
                >
                  <Image label="unsorted" filename={x.n} />
                  {x.s.toFixed(3)}
                </div>)
            })
          }
        </SelectionArea>
      </div>
    </div>
  );

}

export default App;
