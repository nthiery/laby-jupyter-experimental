(*
   Copyright (C) 2007-2010 Stéphane Gimenez
   You have permission to copy, modify, and redistribute under the
   terms of the GPL-3.0. For full license terms, see gpl-3.0.txt.
*)

(**
   ocaml-dtools
   @author Stéphane Gimenez
*)

let log = Log.make ["res"]

type t = string list

type path = string

let conf =
  Conf.void
    (F.x "resources configuration" [])

let conf_domain =
  Conf.string
    ~p:(conf#plug "domain")
    (F.x "ressources domain" [])

let conf_data =
  Conf.void
    ~p:(conf#plug "data")
    (F.x "data ressources" [])

let conf_data_dirs =
  Conf.list
    ~p:(conf_data#plug "dirs") ~d:[]
    (F.x "data paths" [])

let conf_bin =
  Conf.void
    ~p:(conf#plug "bin")
    (F.x "binary ressources" [])

let conf_bin_dirs =
  Conf.list
    ~p:(conf_bin#plug "dirs") ~d:[]
    (F.x "binaries paths" [])

exception Error of F.t

let sep =
  begin match Sys.os_type with
  | "Unix" -> "/"
  | "Cygwin" -> "/"
  | "Win32" -> "\\"
  | _ -> assert false
  end

let path = String.concat sep

let f r = F.string (String.concat "/" r)

let check_file f =
  begin try Sys.file_exists f with
  | Sys_error _ ->
      log#warning (
	F.x "cannot access <path>" [
	  "path", F.string f;
	]
      );
      false
  end

let init_dir =
  Sys.getcwd ()

let sys_data_dir = ref "/usr/share"
let sys_tmp_dir = ref "/tmp"

let data_dirs () =
  let domain = conf_domain#get in
  let sys_data_dirs =
    begin match Sys.os_type with
    | "Unix" | "Cygwin" -> [path [!sys_data_dir; domain]]
    | "Win32" -> [path [init_dir; "data"]]
    | _ -> assert false
    end
  in
  let user_data_dirs =
    begin try
      begin match Sys.os_type with
      | "Unix" | "Cygwin" -> [path [Sys.getenv "HOME"; ".config"; domain]]
      | "Win32" -> [path [Sys.getenv "APPDATA"; domain]]
      | _ -> assert false
      end
    with Not_found -> []
    end
  in
  conf_data_dirs#get @ user_data_dirs @ sys_data_dirs

let get r =
  let resource = path r in
  let raw_dir_dist = data_dirs () in
  let dir_list = List.filter check_file raw_dir_dist in
  let l = List.map (fun s -> s ^ sep ^ resource) dir_list in
  let error () =
    raise (Error (
      F.x "cannot find resource <resource> in: <list>" [
	"resource", f r;
	"list", F.v (List.map F.string raw_dir_dist);
      ]
    ));
  in
  let found x =
    log#debug 2 (
      F.x "found resource <resource> at: <location>" [
	"resource", f r;
	"location", F.q (F.string x);
      ]
    );
  in
  let rec may =
    begin function
    | x :: q ->
	begin try
	  begin match Sys.file_exists x with
	  | true -> found x; x
	  | false -> may q
	  end
	with
	| Sys_error _ -> may q
	end
    | [] -> error ()
    end
  in
  may l

let get_list ?ext r =
  let f = Unix.opendir (get r) in
  let accept e =
    begin match ext with
    | None -> true
    | Some ext ->
	let l = String.length ext + 1 in
	String.length e >= l &&
	  String.sub e (String.length e - l) l = "." ^ ext
    end
  in
  let rec get l =
    begin try
      begin match Unix.readdir f with
      | "." | ".." -> get l
      | e -> get (if accept e then e :: l else l)
      end
    with
    | End_of_file -> l
    end
  in
  let l = get [] in
  Unix.closedir f;
  l

let read_chan filename f =
  begin try
    let file = open_in_bin filename in
    f file;
    close_in file;
  with
  | Sys_error m ->
      log#warning (
	F.x "failed to open file: <path>"
	  ["path", F.string (filename)]
      );
  end

let read_lines file =
  let f = open_in file in
  let input () = try Some (input_line f) with End_of_file -> None in
  let rec aux l =
    begin match input () with
    | Some l' -> aux (l' :: l)
    | None -> List.rev l
    end
  in
  aux []

let read_full file =
  String.concat "\n" (read_lines file) ^ "\n"

let read_blocks file =
  let f = open_in file in
  let input () = try Some (input_line f) with End_of_file -> None in
  let rec aux l ll =
    begin match input () with
    | Some "" -> aux [] (List.rev l :: ll)
    | Some l' -> aux (l' :: l) ll
    | None -> List.rev (List.rev l :: ll)
    end
  in
  let rec find_block blocks s =
    begin match blocks with
    | [] -> None
    | (h :: lines) :: q -> if h = s then Some lines else find_block q s
    | [] :: q -> find_block q s
    end
  in
  find_block (aux [] [])


let scol_regexp = Str.regexp_string ";"
let col_regexp = Str.regexp_string ":"

let sys_bin_dirs =
  begin try
    begin match Sys.os_type with
    | "Win32" -> Str.split scol_regexp (Sys.getenv "PATH")
    | _ -> Str.split col_regexp (Sys.getenv "PATH")
    end
  with
  | Not_found -> []
  end

let exe =
  begin match Sys.os_type with
  | "Win32" -> ".exe"
  | _ -> ""
  end

let get_bin x =
  let rec aux ps =
    begin match ps with
    | [] -> None
    | p :: q ->
	let f = p ^ sep ^ x ^ exe in
	if Sys.file_exists f then Some f else aux q
    end
  in
  aux (conf_bin_dirs#get @ sys_bin_dirs)

let rec mktempdir ident =
  let pid = Unix.getpid () in
  let tmp_dir =
    begin match Sys.os_type with
    | "Unix" | "Cygwin" -> !sys_tmp_dir
    | "Win32" -> Sys.getenv "TEMP"
    | _ -> assert false
    end
  in
  let rec aux seed =
    let dir = path [tmp_dir; Printf.sprintf "%s-%d-%d" ident pid seed] in
    begin try Unix.mkdir dir 0o755; dir with
    | Unix.Unix_error (Unix.EEXIST, _, _) -> aux (seed + 1)
    end
  in
  aux 0

let rmtempdir tmp =
  begin try
    let rm n = Unix.unlink (path [tmp; n]) in
    Array.iter rm (Sys.readdir tmp);
    Unix.rmdir tmp
  with
  | Sys_error _ | Unix.Unix_error _ -> ()
  end
